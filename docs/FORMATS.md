# Super Scribblenauts (USA) data formats

Everything below was reverse-engineered for this hack; entry numbers refer to the `1p` archive.

## Archive: `1i` / `1p`

- `1i`: `u32 count`, then `count + 1` × `u32` offsets into `1p`.
- Each entry is either raw or **LZ10** (`0x10` + u24 decompressed size), followed by **one `0x01`
  marker byte**. The loader rejects compressed entries without the marker (symptom: the asset
  silently fails to load, e.g. a blank START button).
- The game never uses LZ back-references of distance 1; our encoder avoids them too.

## Dictionary (entry 24063 = English nouns)

```
u8   n                     alphabet size (50)
u8   alphabet[n]
u32  word_count
u32  bucket[n*n]           offset of first record whose first two letters are (a, b);
                           bucket[a*n + 0] = first record starting with letter a
records, sorted by name, terminated by 0x00:
  u8  record_len, u8 name_len, name, u32 word_id,
  u8  k, u16 def[k], u16 object_id[k], u8 c[k], u8 d[k]      (struct of arrays)
```

`def` is the pak entry of the object definition. Synonyms share identical meaning bytes, so new
words are added by copying an existing word's tail. Entry **24064** maps `object_id` → offset of
that object's canonical name record and must be updated when records move.

## Level scripts

`u16 count`, `count × (u16 index, u32 offset)` sections; sections interleave languages
EN, FR, PT, ES (English = `index % 4 == 0`). Text lines are `op, u8 len, bytes` with op `0x0e`
(title), `0x0f` (line), `0x0c` (last line); lines are tagged `ci…ic` (centred), max 32 visible chars.
No other length fields: only the section offsets need fixing after a length change.

## String tables

`u8 n`, then newline-terminated strings, `n` per language, English first (menus, merits, results).

## Sprite images (objects, UI pictures)

```
u8  ncolours, u16 bgr555[ncolours]     colour 0 = transparent (magenta)
u8  w, u8 h                            or: 0x00, u16 w, u16 h for large images
pixels: 4bpp (ncolours <= 16) or 8bpp, row-major, low nibble first
```

Characters are **puppets**: one sheet holds head, torso, arms and legs at fixed boxes, and the
engine animates them. Maxwell = 8914/8915/8916 (64×64): head 28×25 @ (0,0), torso 15×14 @ (0,26),
front arm 7×16 @ (19,26), back arm 7×15 @ (27,36), legs 8×14 @ (0,41) and (11,41).

## Title screen (sub engine, BG0–BG2, 8bpp, shared tile block)

| Layer | Map entry | Notes |
|-------|-----------|-------|
| BG0 gingham | 24339 | 32×32 |
| BG1 logo | 24343 | 32×24 |
| BG2 pegasus | 27467 | 32×32, absolute tile numbers |

Tiles: 24342 (all layers), palette: 24344 (256 colours, **shared with other top screens**:
original slots must keep their indices; slots 113–255 are free). Menus place the maps at
`0x6800`, so the shared tile block must stay ≤ 416 tiles.

## UI sprite containers (641 of them)

`u32 ncer_off, u32 ncgr_off, u32 nanr_off|end, u32 end`, then Nintendo NCER (`RECN`/`KBEC`),
NCGR (`RGCN`/`RAHC`) and optionally NANR sections. Palettes are separate NCLR files
(743, 762–764, 923, 962–968, 995–996, 29061, 29967, 31817, 33322).
