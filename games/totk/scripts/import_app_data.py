"""Recover verified work files from a packaged Mac app, including pre-game-data builds.

Only repository-pinned game modules and images are accepted. Legacy tables are read
as data from the old Mach-O; the old executable is never loaded or run. Generated
tables, indexes and game bytes belong exclusively in the ignored work folder.
"""
import json
import re
import struct
import subprocess
from pathlib import PurePosixPath

import build_app as build


def need(condition, message):
    if not condition:
        raise build.BuildError(f'cannot import app: {message}')


def romfs_manifest(data, size, digest):
    """Decode the shipped TOTKRFS1 index, with the same bounds as the native reader."""
    need(len(data) >= 24, 'truncated RomFS index')
    magic, count, strings = struct.unpack_from('<8sQQ', data)
    need(magic == b'TOTKRFS1' and 0 < count <= (len(data) - 24) // 24
         and strings == 24 + count * 24, 'invalid RomFS index header')
    files, seen = [], set()
    for i in range(count):
        offset, length, name, n = struct.unpack_from('<QQII', data, 24 + i * 24)
        start = strings + name
        need(n > 1 and start <= len(data) and n <= len(data) - start
             and data[start + n - 1] == 0, 'RomFS name outside index')
        try:
            path = data[start:start + n - 1].decode('utf-8')
        except UnicodeError:
            raise build.BuildError('cannot import app: invalid UTF-8 RomFS path') from None
        p = PurePosixPath(path)
        need(path and '\0' not in path and not p.is_absolute() and '..' not in p.parts
             and p.as_posix() == path and path not in seen, 'invalid or duplicate RomFS path')
        need(offset <= size and length <= size - offset, 'RomFS entry outside image')
        seen.add(path)
        files.append(dict(path=path, offset=offset, size=length))
    return dict(status='pass', romfs_size=size, romfs_sha256=digest, files=files,
                integrity='packaged image SHA-256 matched repository pin')


class LegacyMachO:
    """Bounded arm64 Mach-O reads; Apple's dyld_info resolves chained rebases."""
    def __init__(self, path):
        self.data = path.read_bytes()
        need(len(self.data) >= 32, 'truncated legacy executable')
        magic, cpu, _, _, count, commands, _, _ = struct.unpack_from('<8I', self.data)
        need(magic == 0xfeedfacf and cpu == 0x100000c and commands <= len(self.data) - 32
             and count <= commands // 8, 'legacy executable must be thin arm64 Mach-O')
        self.segments = []
        symtab = None
        cursor, end = 32, 32 + commands
        for _ in range(count):
            need(cursor + 8 <= end, 'truncated Mach-O load command')
            cmd, size = struct.unpack_from('<II', self.data, cursor)
            need(size >= 8 and size <= end - cursor, 'invalid Mach-O load command')
            if cmd == 0x19:  # LC_SEGMENT_64, mach-o/loader.h
                need(size >= 72, 'truncated Mach-O segment')
                vm, _, off, length = struct.unpack_from('<4Q', self.data, cursor + 24)
                need(off <= len(self.data) and length <= len(self.data) - off, 'segment outside file')
                if length:
                    self.segments.append((vm, off, length))
            elif cmd == 2:  # LC_SYMTAB
                need(size >= 24, 'truncated Mach-O symbol command')
                symtab = struct.unpack_from('<4I', self.data, cursor + 8)
            cursor += size
        need(symtab is not None, 'legacy executable has no symbol table')
        off, count, strings, length = symtab
        need(off <= len(self.data) and count <= (len(self.data) - off) // 16
             and strings <= len(self.data) and length <= len(self.data) - strings,
             'symbol table outside executable')
        self.symbols = {}
        for i in range(count):
            name, kind, _, _, value = struct.unpack_from('<IBBHQ', self.data, off + i * 16)
            if kind & 0xe0 or not kind & 0x0e:  # skip STAB/debug and undefined entries
                continue
            need(name < length, 'symbol name outside string table')
            stop = self.data.find(b'\0', strings + name, strings + length)
            need(stop >= 0, 'unterminated Mach-O symbol')
            if self.data[strings + name:stop] == b'_modules':
                need('_modules' not in self.symbols, 'ambiguous legacy modules symbol')
                self.symbols['_modules'] = value
        self.rebases = {}
        result = subprocess.run(['xcrun', 'dyld_info', '-fixups', str(path)],
                                capture_output=True, text=True, timeout=60)
        need(result.returncode == 0, 'dyld_info could not read legacy pointer fixups')
        for line in result.stdout.splitlines():
            row = re.fullmatch(r'\s+\S+\s+\S+\s+(0x[0-9A-Fa-f]+)\s+rebase\s+(0x[0-9A-Fa-f]+)\s*', line)
            if row:
                self.rebases[int(row[1], 16)] = int(row[2], 16)

    def read(self, address, size):
        for vm, off, length in self.segments:
            if address >= vm and address - vm <= length and size <= length - (address - vm):
                return self.data[off + address - vm:off + address - vm + size]
        raise build.BuildError('cannot import app: legacy address outside file-backed segment')

    def pointer(self, address):
        raw, = struct.unpack('<Q', self.read(address, 8))
        value = self.rebases.get(address, raw)
        self.read(value, 1)
        return value

    def string(self, address):
        for vm, off, length in self.segments:
            if vm <= address < vm + length:
                data = self.read(address, min(65536, vm + length - address))
                stop = data.find(b'\0')
                need(stop >= 0, 'unterminated legacy string')
                try:
                    return data[:stop].decode('utf-8')
                except UnicodeError:
                    break
        raise build.BuildError('cannot import app: invalid legacy string')


def legacy_tables(binary, modules, version):
    """Convert the pre-1cbe2a1 192-byte Module ABI to the current pointer-free format."""
    image = LegacyMachO(binary)
    base = image.symbols.get('_modules')
    need(base is not None, 'legacy executable has no modules array; its original work folder is needed')
    arrays, strings, records = bytearray(), bytearray(), []
    probe_plt = probe_slot = None

    def place(data):
        arrays.extend(bytes(-len(arrays) % 8))
        offset = 64 + 3 * 208 + len(arrays)
        arrays.extend(data)
        return offset

    for i, (name, module) in enumerate(modules.items()):
        address = base + i * 192
        raw = image.read(address, 192)
        need(image.string(image.pointer(address)) == name, 'legacy module order differs')
        need(image.string(image.pointer(address + 8)) == build.sha256(module), 'legacy module hash differs')
        file_size, mapped_size, *layout = struct.unpack_from('<11Q', raw, 16)
        text, ro, data, patch, key, init, ctor, init_array, init_size = layout
        need(file_size == module.stat().st_size and mapped_size == 0
             and 0 < text <= ro <= data <= key <= patch <= file_size
             and data <= ctor < key and init < text and init_array <= file_size
             and init_size <= file_size - init_array, 'legacy module layout differs')
        nsym, nreloc, ngate = (struct.unpack_from('<I', raw, off)[0] for off in (112, 128, 144))
        need(0 < nsym < 1000000 and nreloc < 1000000 and ngate < 1000000,
             'legacy metadata count outside bounds')
        symbol_base, reloc_base, gate_base = (image.pointer(address + off) for off in (104, 120, 136))
        symbols, names = bytearray(), []
        for j in range(nsym):
            at = symbol_base + j * 40
            _, value, length, defined, binding, kind = struct.unpack('<QQQIII4x', image.read(at, 40))
            symbol = image.string(image.pointer(at))
            need(defined in (0, 1) and binding < 256 and kind < 256, 'invalid legacy symbol')
            names.append(symbol)
            symbols.extend(struct.pack('<QQIBBBx', value, length, len(strings), defined, binding, kind))
            strings.extend(symbol.encode() + b'\0')
        relocs = image.read(reloc_base, nreloc * 24)
        slots = []
        for where, kind, symbol, addend in struct.iter_unpack('<QIIq', relocs):
            need(data <= where <= key - 8 and symbol < nsym and kind in (257, 1025, 1026, 1027),
                 'invalid legacy relocation')
            if kind == 1026 and names[symbol] == '_ZN2nn2os13GetSystemTickEv':
                slots.append(where)
        gates = image.read(gate_base, ngate * 24)
        last = -1
        for ret, original, timer, arg in struct.iter_unpack('<QQII', gates):
            need(last < ret < file_size and original < text and timer <= 2, 'invalid legacy gate')
            last = ret
        if i == 0:
            need(len(slots) == 1, 'ambiguous system-tick relocation')
            probe_slot = slots[0]
            main = module.read_bytes()
            matches = []
            for at in range(max(0, text - 0x10000), text - 12, 4):
                a, b, _, d = struct.unpack_from('<4I', main, at)
                if a & 0x9f00001f != 0x90000010 or b & 0xffc003ff != 0xf9400211 or d != 0xd61f0220:
                    continue
                imm = ((a >> 29) & 3) | (((a >> 5) & 0x7ffff) << 2)
                imm = (imm ^ (1 << 20)) - (1 << 20)
                if (at & ~4095) + (imm << 12) + ((b >> 10) & 0xfff) * 8 == probe_slot:
                    matches.append(at)
            need(len(matches) == 1, 'ambiguous original system-tick PLT')
            probe_plt = matches[0]
        records.append(struct.pack('<16s72s13Q4I', name.encode(), build.sha256(module).encode(),
                                   file_size, *layout[:5], init, ctor, init_array, init_size,
                                   place(symbols), place(relocs), place(gates), nsym, nreloc, ngate, 0))
    arrays.extend(bytes(-len(arrays) % 8))
    offset = 64 + 3 * 208 + len(arrays)
    header = struct.pack('<8s8sII5Q', b'TOTKTAB1', version.encode(), 3, 1, probe_plt, probe_slot,
                         offset, len(strings), offset + len(strings))
    return header + b''.join(records) + arrays + strings


def import_app(app, tree, version, expected):
    """Restore work files without changing the source app or recording invented provenance."""
    res = app / 'Contents/Resources/totk'
    modules = {name: res / f'rewritten/{version}/{name}.patched.bin' for name in ('main', 'subsdk0', 'sdk')}
    for name, path in modules.items():
        need(path.is_file() and build.sha256(path) == expected['rewritten_sha256'][path.name],
             f'{name} is not the repository-pinned rewrite')
    data = tree / f'build/game-data/{version}'
    installed = res / f'build/game-data/{version}'
    tables = ((installed / 'runtime-tables.bin').read_bytes() if (installed / 'runtime-tables.bin').is_file()
              else legacy_tables(res / 'build/totk-native', modules, version))
    # Generate every index from the packaged bounded index, after hashing its image against the pin.
    configs, pending = {}, []
    volumes = [(f'extracted/{version}/romfs', expected['romfs'], None)]
    if version.startswith('botw'):
        volumes += [(f'extracted/{version}/aoc/{i}', pin, int(i)) for i, pin in expected.get('aoc', {}).items()
                    if (res / f'extracted/{version}/aoc/{i}/romfs.bin').is_file()]
    aoc = []
    for rel, pin, index in volumes:
        source = res / rel
        build.say(f'importing verified app data: {rel}')
        need((source / 'romfs.bin').stat().st_size == pin['size'] and build.sha256(source / 'romfs.bin') == pin['sha256'],
             f'{rel} image does not match repository pin')
        raw = (source / 'runtime-index.bin').read_bytes()
        manifest = romfs_manifest(raw, pin['size'], pin['sha256'])
        if 'files' in pin:
            need(len(manifest['files']) == pin['files'], f'{rel} file count differs')
        if index is not None:
            manifest['index'] = index
            aoc.append(index)
        prefix = 'ROMFS' if index is None else f'AOC{index}'
        configs[prefix] = (f'{prefix}_IMAGE_SIZE {pin["size"]}\n{prefix}_IMAGE_SHA256 {pin["sha256"]}\n'
                           f'{prefix}_INDEX_SHA256 {build.sha256(source / "runtime-index.bin")}\n')
        pending.append((rel, manifest))
    fonts = res / 'extracted/firmware/shared-fonts'
    report = build.font_report(fonts)
    font_lines = []
    for f in report['fonts']:
        i = f['type']
        filename = f'{i}-{f["name"]}.bfttf'
        font_lines.append(f'FONT{i}_FILE {filename}\nFONT{i}_FILE_BYTES {f["bfttf_bytes"]}\n'
                          f'FONT{i}_FONT_BYTES {f["font_bytes"]}\nFONT{i}_SHA256 {f["sha256"]}\n')
    for name, source in modules.items():
        build.clone(source, tree / f'rewritten/{version}/{name}.patched.bin')
    for rel, manifest in pending:
        for filename in ('romfs.bin', 'runtime-index.bin'):
            build.clone(res / rel / filename, tree / rel / filename)
        (tree / rel / 'index.json').write_text(json.dumps(manifest, indent=2) + '\n')
    build.copy_tree(fonts, tree / 'extracted/firmware/shared-fonts')
    data.mkdir(parents=True, exist_ok=True)
    (data / 'runtime-tables.bin').write_bytes(tables)
    (data / 'romfs-config.txt').write_text(configs['ROMFS'])
    (data / 'shared-fonts.txt').write_text(''.join(font_lines))
    # The old rewriter's identity is unknown. check_rewriter accepts these modules by their exact pinned hashes.
    (data / 'rewriter.txt').write_text('# Imported repository-pinned rewrites; original rewriter identity unavailable.\n'
                                      'REWRITER_SHA256 unknown\n')
    if version.startswith('botw'):
        (data / 'aoc-config.txt').write_text(f'AOC_PRESENT_MASK {sum(1 << (i - 1) for i in aoc)}\n'
                                           + ''.join(configs[f'AOC{i}'] for i in sorted(aoc)))
    build.say('verified work data imported from the app; no game container or keys used')
