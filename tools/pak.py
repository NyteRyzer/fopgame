"""Read/write Super Scribblenauts' 1i (index) + 1p (pack) archive inside the ROM."""
import struct
import ndspy.rom
import ndspy.lz10 as lz10
import lz10 as lz10x


class Pak:
    def __init__(self, rom_path):
        self.rom = ndspy.rom.NintendoDSRom.fromFile(rom_path)
        self.idx_id = self.rom.filenames.idOf('1i')
        self.pak_id = self.rom.filenames.idOf('1p')
        idx = bytes(self.rom.files[self.idx_id])
        pak = bytes(self.rom.files[self.pak_id])
        n = struct.unpack_from('<I', idx, 0)[0]
        offs = struct.unpack_from('<%dI' % (n + 1), idx, 4)
        self.raw = [pak[offs[i]:offs[i + 1]] for i in range(n)]
        self.changed = {}

    def get(self, i):
        """Decompressed contents of entry i (and whether it was compressed)."""
        if i in self.changed:
            return self.changed[i][0], self.changed[i][1]
        b = self.raw[i]
        if len(b) >= 4 and b[0] == 0x10:
            try:
                d = lz10.decompress(b)
                if len(d) == struct.unpack_from('<I', b, 0)[0] >> 8:
                    return bytes(d), True
            except Exception:
                pass
        return b, False

    def set(self, i, data):
        _, comp = self.get(i)
        self.changed[i] = (bytes(data), comp)

    def save(self, out_path):
        raw = list(self.raw)
        for i, (data, comp) in self.changed.items():
            # Every compressed entry ends with a 0x01 marker byte after the LZ10
            # stream; the game's loader silently skips entries without it.
            raw[i] = lz10x.compress(data) + b'\x01' if comp else data
        offs = [0]
        for b in raw:
            offs.append(offs[-1] + len(b))
        self.rom.files[self.idx_id] = struct.pack('<I', len(raw)) + struct.pack('<%dI' % len(offs), *offs)
        self.rom.files[self.pak_id] = b''.join(raw)
        self.rom.saveToFile(out_path)
