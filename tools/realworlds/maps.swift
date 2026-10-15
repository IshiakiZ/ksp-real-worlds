// Real Worlds' textures, made from NASA's, NOAA's and the USGS's global maps (2026-10-14).
//
//     swift -O tools/realworlds/maps.swift jobs.json      (or: swiftc -O -o maps tools/realworlds/maps.swift; ./maps jobs.json)
//
// jobs.json is a list of jobs, each one of:
//   {"kind": "height", "in": "dem.tif", "out": "Earth_height.dds", "width": 8192, "height": 4096,
//    "lon0": -180, "scale": 1, "add": 0, "low": -11000, "high": 9000,
//    "raw": {"width": 5760, "height": 2880, "type": "int16be"}}     (raw only for a headerless file, as MOLA's .img)
//      heights in metres (the file's value times scale plus add), stored as 16-bit fractions of low..high (R16 DDS);
//      the job's report gives what the config needs: offset = low, deformity = high - low.
//   {"kind": "colour", "in": "map.tif", "out": "Earth_colour.dds", "width": 8192, "height": 4096, "lon0": -180,
//    "grey": false, "tint": [1, 1, 1], "gamma": 1, "mips": true}       (BC1 DDS, with mipmaps)
//   {"kind": "normals", "in": "dem.tif", "out": "Earth_normals.dds", "width": 4096, "height": 2048, "lon0": -180,
//    "scale": 1, "add": 0, "radius": 6371008.4, "strength": 1}       (DXT5 DDS, x in alpha and y in green, as KSP's
//      shaders read a normal map)
// Every map is equirectangular: north at its top, its left edge at longitude lon0 (degrees east), east to the right.
// The textures are written for the game's own way of laying a map on a world (see "KSP's longitude" below).
import Foundation
import ImageIO
import CoreGraphics

// MARK: - KSP's longitude
// A terrain's map is read at u = atan2(x, z) / 2 pi, in the world's own frame, where the game's longitude is
// atan2(z, x) (PQS.BuildVertexMapCoords and CelestialBody.GetLongitude, decompiled): so u = 0.25 - longitude / 360,
// running west as longitude runs east, and longitude 0 at a quarter of the way across. And a DDS's first row is the
// texture's bottom (the south pole, v = 0) as Unity loads it. Both are settable per job ("mirror", "flipRows"), in case a
// test in the game says otherwise.

struct Job: Decodable {
    var kind: String
    var `in`: String
    var out: String
    var width: Int
    var height: Int
    var lon0: Double?
    var scale: Double?
    var add: Double?
    var low: Double?
    var high: Double?
    var raw: Raw?
    var grey: Bool?
    var tint: [Double]?
    var gamma: Double?
    var mips: Bool?
    var radius: Double?
    var strength: Double?
    var mirror: Bool?
    var flipRows: Bool?
    var nodata: Double?
    var dropLast: Bool?
    var deep: Bool?
    var floorAt: Double?   // (normals: heights below this are taken as this, as the sea's level for the sea floor)
    struct Raw: Decodable { var width: Int; var height: Int; var type: String }
}

/// An image as floats: w by h, c channels, rows from the top (north) down.
final class Picture {
    let w: Int, h: Int, c: Int
    var px: [Float]
    init(w: Int, h: Int, c: Int, fill: Float = 0) { self.w = w; self.h = h; self.c = c; px = [Float](repeating: fill, count: w * h * c) }
}

func fail(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(1) }

// MARK: - reading: TIFF (uncompressed, strips or tiles, classic or BigTIFF), raw grids, and anything ImageIO reads

struct TiffInfo {
    var width = 0, height = 0, bits = 8, samples = 1, compression = 1, format = 1, planar = 1
    var stripOffsets: [Int] = [], stripCounts: [Int] = [], rowsPerStrip = 0
    var tileW = 0, tileH = 0, tileOffsets: [Int] = [], tileCounts: [Int] = []
    var littleEndian = true
    var pixelScale: [Double] = [], tiepoint: [Double] = []   // GeoTIFF: the size of a pixel, and where the first one is
}

func readTiffInfo(_ d: Data) -> TiffInfo? {
    guard d.count > 16 else { return nil }
    var t = TiffInfo()
    let b0 = d[0], b1 = d[1]
    if b0 == 0x49 && b1 == 0x49 { t.littleEndian = true } else if b0 == 0x4D && b1 == 0x4D { t.littleEndian = false } else { return nil }
    func u16(_ o: Int) -> Int { let a = Int(d[o]), b = Int(d[o + 1]); return t.littleEndian ? a | b << 8 : a << 8 | b }
    func u32(_ o: Int) -> Int { t.littleEndian ? u16(o) | u16(o + 2) << 16 : u16(o) << 16 | u16(o + 2) }
    func u64(_ o: Int) -> Int { t.littleEndian ? u32(o) | u32(o + 4) << 32 : u32(o) << 32 | u32(o + 4) }
    let version = u16(2)
    let big = version == 43
    guard version == 42 || big else { return nil }
    let ifd = big ? u64(8) : u32(4)
    let count = big ? u64(ifd) : u16(ifd)
    let entrySize = big ? 20 : 12
    let first = ifd + (big ? 8 : 2)
    for i in 0..<count {
        let e = first + i * entrySize
        let tag = u16(e), type = u16(e + 2)
        let n = big ? u64(e + 4) : u32(e + 4)
        let size = [0, 1, 1, 2, 4, 8, 1, 1, 2, 4, 8, 4, 8, 4, 0, 0, 8, 8, 8][min(type, 18)]
        let inline = n * size <= (big ? 8 : 4)
        let at = inline ? e + (big ? 12 : 8) : (big ? u64(e + 12) : u32(e + 8))
        func value(_ k: Int) -> Int {
            switch type {
            case 3: return u16(at + 2 * k)
            case 4: return u32(at + 4 * k)
            case 16: return u64(at + 8 * k)
            default: return size == 1 ? Int(d[at + k]) : u32(at + 4 * k)
            }
        }
        func values() -> [Int] { (0..<n).map(value) }
        func doubles() -> [Double] {
            (0..<n).map { k -> Double in
                var v: UInt64 = 0
                for b in 0..<8 { v |= UInt64(d[at + 8 * k + b]) << UInt64(8 * (t.littleEndian ? b : 7 - b)) }
                return Double(bitPattern: v)
            }
        }
        switch tag {
        case 33550: if type == 12 { t.pixelScale = doubles() }
        case 33922: if type == 12 { t.tiepoint = doubles() }
        case 256: t.width = value(0)
        case 257: t.height = value(0)
        case 258: t.bits = value(0)
        case 259: t.compression = value(0)
        case 273: t.stripOffsets = values()
        case 277: t.samples = value(0)
        case 278: t.rowsPerStrip = value(0)
        case 279: t.stripCounts = values()
        case 284: t.planar = value(0)
        case 322: t.tileW = value(0)
        case 323: t.tileH = value(0)
        case 324: t.tileOffsets = values()
        case 325: t.tileCounts = values()
        case 339: t.format = value(0)
        default: break
        }
    }
    return t
}

/// One sample at a byte offset, as a float.
@inline(__always) func sample(_ p: UnsafeRawBufferPointer, _ o: Int, bits: Int, format: Int, little: Bool) -> Float {
    switch (bits, format) {
    case (8, _): return Float(p[o])
    case (16, 2):
        let v = little ? UInt16(p[o]) | UInt16(p[o + 1]) << 8 : UInt16(p[o]) << 8 | UInt16(p[o + 1])
        return Float(Int16(bitPattern: v))
    case (16, _):
        let v = little ? UInt16(p[o]) | UInt16(p[o + 1]) << 8 : UInt16(p[o]) << 8 | UInt16(p[o + 1])
        return Float(v)
    case (32, 3):
        var v = UInt32(p[o]) | UInt32(p[o + 1]) << 8 | UInt32(p[o + 2]) << 16 | UInt32(p[o + 3]) << 24
        if !little { v = v.byteSwapped }
        return Float(bitPattern: v)
    case (32, 2):
        var v = UInt32(p[o]) | UInt32(p[o + 1]) << 8 | UInt32(p[o + 2]) << 16 | UInt32(p[o + 3]) << 24
        if !little { v = v.byteSwapped }
        return Float(Int32(bitPattern: v))
    default: fail("a sample of \(bits) bits, format \(format), is not read here")
    }
}

/// The longitude of a GeoTIFF's left edge, from its tags (degrees, or metres of an equidistant map round a sphere whose
/// circumference its width spans); nil where it has none.
func geoLeftEdge(_ path: String) -> Double? {
    guard let d = try? Data(contentsOf: URL(fileURLWithPath: path), options: .alwaysMapped), let t = readTiffInfo(d),
          t.pixelScale.count >= 2, t.tiepoint.count >= 6 else { return nil }
    let sx = t.pixelScale[0], x0 = t.tiepoint[3] - t.tiepoint[0] * sx
    let span = sx * Double(t.width)
    if abs(span - 360) < 1 || sx < 1 { return x0 }               // degrees
    return x0 / span * 360                                       // metres round the world
}

/// A map read a row at a time (the big ones are read straight from the file, never whole).
protocol Rows {
    var w: Int { get }
    var h: Int { get }
    var c: Int { get }
    func row(_ y: Int, into out: inout [Float])
}

/// An uncompressed TIFF in strips, its samples interleaved or each in a plane of its own.
final class TiffRows: Rows {
    let d: Data, t: TiffInfo, w: Int, h: Int, c: Int, bytes: Int, rps: Int
    init?(_ path: String) {
        guard let d = try? Data(contentsOf: URL(fileURLWithPath: path), options: .alwaysMapped), let t = readTiffInfo(d),
              t.compression == 1, t.tileW == 0, !t.stripOffsets.isEmpty else { return nil }
        self.d = d; self.t = t; w = t.width; h = t.height; c = t.samples; bytes = t.bits / 8
        rps = t.rowsPerStrip > 0 ? t.rowsPerStrip : t.height
    }
    func row(_ y: Int, into out: inout [Float]) {
        let t = self.t, w = self.w, c = self.c, bytes = self.bytes, rps = self.rps
        d.withUnsafeBytes { (p: UnsafeRawBufferPointer) in
            if t.planar == 1 || c == 1 {
                let k = y / rps, off = t.stripOffsets[k] + (y - k * rps) * w * c * bytes
                for i in 0..<(w * c) { out[i] = sample(p, off + i * bytes, bits: t.bits, format: t.format, little: t.littleEndian) }
            } else {
                let perPlane = (h + rps - 1) / rps
                for s in 0..<c {
                    let k = s * perPlane + y / rps, off = t.stripOffsets[k] + (y % rps) * w * bytes
                    for x in 0..<w { out[x * c + s] = sample(p, off + x * bytes, bits: t.bits, format: t.format, little: t.littleEndian) }
                }
            }
        }
    }
}

/// A headerless grid (MOLA's .img).
final class RawRows: Rows {
    let d: Data, w: Int, h: Int, c = 1, bits: Int, format: Int, little: Bool
    init(_ path: String, _ r: Job.Raw) {
        guard let d = try? Data(contentsOf: URL(fileURLWithPath: path), options: .alwaysMapped) else { fail("cannot read \(path)") }
        self.d = d; w = r.width; h = r.height
        switch r.type {
        case "int16be": (bits, format, little) = (16, 2, false)
        case "int16le": (bits, format, little) = (16, 2, true)
        case "uint16be": (bits, format, little) = (16, 1, false)
        case "float32le": (bits, format, little) = (32, 3, true)
        case "float32be": (bits, format, little) = (32, 3, false)
        default: fail("raw type \(r.type)?")
        }
        guard d.count >= w * h * bits / 8 else { fail("\(path) is shorter than \(w) x \(h)") }
    }
    func row(_ y: Int, into out: inout [Float]) {
        let w = self.w, bits = self.bits, format = self.format, little = self.little
        d.withUnsafeBytes { p in for x in 0..<w { out[x] = sample(p, (y * w + x) * bits / 8, bits: bits, format: format, little: little) } }
    }
}

/// Anything ImageIO opens (a compressed TIFF, a JPEG): decoded whole, then given out a row at a time; 0..255, or
/// 0..65535 for 16 bits a sample.
final class ImageRows: Rows {
    let w: Int, h: Int, c: Int, deep: Bool, comps: Int, rowBytes: Int
    var buf: [UInt8]
    init(_ path: String, grey: Bool) {
        guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, [kCGImageSourceShouldCache: false] as CFDictionary),
              let img = CGImageSourceCreateImageAtIndex(src, 0, [kCGImageSourceShouldCache: false] as CFDictionary) else { fail("ImageIO cannot open \(path)") }
        w = img.width; h = img.height
        deep = img.bitsPerComponent > 8
        comps = grey ? 1 : 4
        c = grey ? 1 : 3
        let bpc = deep ? 16 : 8
        rowBytes = w * comps * bpc / 8
        buf = [UInt8](repeating: 0, count: rowBytes * h)
        let space = grey ? CGColorSpaceCreateDeviceGray() : CGColorSpace(name: CGColorSpace.sRGB)!
        let info: UInt32 = (grey ? CGImageAlphaInfo.none.rawValue : CGImageAlphaInfo.noneSkipLast.rawValue) | (deep ? CGBitmapInfo.byteOrder16Little.rawValue : 0)
        let (ww, hh, rb, dp) = (w, h, rowBytes, deep)
        buf.withUnsafeMutableBytes { m in
            guard let ctx = CGContext(data: m.baseAddress, width: ww, height: hh, bitsPerComponent: dp ? 16 : 8, bytesPerRow: rb, space: space, bitmapInfo: info) else { fail("no drawing context for \(path)") }
            ctx.interpolationQuality = .none
            ctx.draw(img, in: CGRect(x: 0, y: 0, width: ww, height: hh))
        }
    }
    func row(_ y: Int, into out: inout [Float]) {
        let w = self.w, c = self.c, comps = self.comps, deep = self.deep, base = y * rowBytes
        buf.withUnsafeBytes { p in
            for x in 0..<w { for s in 0..<c {
                let o = base + (x * comps + s) * (deep ? 2 : 1)
                out[x * c + s] = deep ? Float(UInt16(p[o]) | UInt16(p[o + 1]) << 8) : Float(p[o])
            } }
        }
    }
}

func rows(_ j: Job, grey: Bool) -> Rows {
    if let r = j.raw { return RawRows(j.in, r) }
    let lower = j.in.lowercased()
    if lower.hasSuffix(".tif") || lower.hasSuffix(".tiff"), let t = TiffRows(j.in) { return t }
    return ImageRows(j.in, grey: grey)
}

/// The map resampled to w by h by area (each source pixel counted by the share of it under each new one), read a row at
/// a time; out channels 1 (grey: the mean of the source's first three) or 3; values through `value`. Pixels the source
/// marks as having no data (every channel equal to nodata) are left out, and what they leave empty is filled from round
/// about. dropLast: a grid-registered map, whose last column and row repeat its first.
func resampled(_ src: Rows, w nw: Int, h nh: Int, channels oc: Int, nodata: Float?, dropLast: Bool, value: (Float) -> Float) -> Picture {
    let sw = dropLast ? src.w - 1 : src.w, sh = dropLast ? src.h - 1 : src.h
    // across: for each new column, its first source column and the weights of those under it
    var firsts = [Int](), counts = [Int](), weights = [[Float]]()
    let rx = Double(sw) / Double(nw)
    for i in 0..<nw {
        let a = Double(i) * rx, b = Double(i + 1) * rx
        let f = Int(floor(a)), l = min(sw - 1, Int(ceil(b)) - 1)
        var wts: [Float] = []
        for k in f...max(f, l) { wts.append(Float(min(b, Double(k + 1)) - max(a, Double(k)))) }
        firsts.append(f); counts.append(wts.count); weights.append(wts)
    }
    let ry = Double(sh) / Double(nh)
    let out = Picture(w: nw, h: nh, c: oc)
    var wsum = [Float](repeating: 0, count: nw * nh)
    var line = [Float](repeating: 0, count: src.w * src.c)
    var conv = [Float](repeating: 0, count: sw * oc)
    var valid = [Bool](repeating: true, count: sw)
    var across = [Float](repeating: 0, count: nw * oc)
    var acrossW = [Float](repeating: 0, count: nw)
    for y in 0..<sh {
        src.row(y, into: &line)
        for x in 0..<sw {
            var bad = nodata != nil
            if let nd = nodata { for s in 0..<src.c where line[x * src.c + s] != nd { bad = false; break } }
            valid[x] = !bad
            if oc == 1 {
                var m: Float = 0
                let n = min(3, src.c)
                for s in 0..<n { m += line[x * src.c + s] }
                conv[x] = value(m / Float(n))
            } else {
                for s in 0..<3 { conv[x * 3 + s] = value(line[x * src.c + min(s, src.c - 1)]) }
            }
        }
        for i in 0..<nw {
            var sw0: Float = 0
            for ch in 0..<oc { across[i * oc + ch] = 0 }
            let f = firsts[i], wts = weights[i]
            for k in 0..<counts[i] where valid[f + k] {
                for ch in 0..<oc { across[i * oc + ch] += conv[(f + k) * oc + ch] * wts[k] }
                sw0 += wts[k]
            }
            acrossW[i] = sw0
        }
        // down: this source row's share of each new row it lies under
        let y0 = Double(y), y1 = Double(y + 1)
        var r = Int(floor(y0 / ry))
        while r < nh && Double(r) * ry < y1 {
            let share = Float(min(y1, Double(r + 1) * ry) - max(y0, Double(r) * ry))
            if share > 0 {
                for i in 0..<nw where acrossW[i] > 0 {
                    for ch in 0..<oc { out.px[(r * nw + i) * oc + ch] += across[i * oc + ch] * share }
                    wsum[r * nw + i] += acrossW[i] * share
                }
            }
            r += 1
        }
    }
    var empty = 0
    for i in 0..<(nw * nh) {
        if wsum[i] > 0 { for ch in 0..<oc { out.px[i * oc + ch] /= wsum[i] } } else { for ch in 0..<oc { out.px[i * oc + ch] = .nan }; empty += 1 }
    }
    if empty > 0 { fillGaps(out); print("  \(empty) pixels had no data and were filled from round about") }
    return out
}

/// Pixels with no value (NaN) take the mean of their neighbours that have one, ring by ring inwards. Ring by ring alone,
/// each column of a map grows from its own edge pixel, and a large unseen region (Triton's north, Pluto's and Charon's
/// south) showed as streaks running to the pole; so each filled pixel is then smoothed along its row, the more the deeper
/// it lies in the gap, and drawn towards the mean of what was measured: an unseen cap reads as a plain one.
func fillGaps(_ p: Picture) {
    let n = p.w * p.h
    var depth = [Int](repeating: 0, count: n)          // 0: measured; k: filled in the k-th ring
    var mean = [Double](repeating: 0, count: p.c), seen = 0.0
    for i in 0..<n where !p.px[i * p.c].isNaN { for ch in 0..<p.c { mean[ch] += Double(p.px[i * p.c + ch]) }; seen += 1 }
    if seen == 0 { return }
    for ch in 0..<p.c { mean[ch] /= seen }
    var ring = 0, left = true
    while left {
        left = false
        ring += 1
        var next = p.px
        for y in 0..<p.h { for x in 0..<p.w where p.px[(y * p.w + x) * p.c].isNaN {
            var s = [Float](repeating: 0, count: p.c), k: Float = 0
            for dy in -1...1 { for dx in -1...1 where dx != 0 || dy != 0 {
                let yy = y + dy
                if yy < 0 || yy >= p.h { continue }
                let xx = (x + dx + p.w) % p.w
                let o = (yy * p.w + xx) * p.c
                if p.px[o].isNaN { continue }
                for ch in 0..<p.c { s[ch] += p.px[o + ch] }
                k += 1
            } }
            if k > 0 { for ch in 0..<p.c { next[(y * p.w + x) * p.c + ch] = s[ch] / k }; depth[y * p.w + x] = ring } else { left = true }
        } }
        p.px = next
    }
    // (along each row, round the world: the mean over a reach that grows with the depth, and the measured mean deeper in)
    let deep = Double(max(8, p.h / 24))
    var out = p.px
    var pre = [Double](repeating: 0, count: (2 * p.w + 1) * p.c)
    for y in 0..<p.h {
        var any = false
        for x in 0..<p.w where depth[y * p.w + x] > 0 { any = true; break }
        if !any { continue }
        for i in 0..<(2 * p.w) { for ch in 0..<p.c { pre[(i + 1) * p.c + ch] = pre[i * p.c + ch] + Double(p.px[(y * p.w + i % p.w) * p.c + ch]) } }
        for x in 0..<p.w where depth[y * p.w + x] > 0 {
            let d = Double(depth[y * p.w + x])
            let r = min(p.w / 2 - 1, Int(d * 6))
            let a = x - r + p.w, b = x + r + p.w + 1          // [a, b) in the doubled row, shifted by w to stay positive
            let lo = a % (2 * p.w), span = b - a
            let t0 = min(1.0, d / deep), t = t0 * t0 * (3 - 2 * t0)
            for ch in 0..<p.c {
                var sum: Double
                if lo + span <= 2 * p.w { sum = pre[(lo + span) * p.c + ch] - pre[lo * p.c + ch] }
                else { sum = pre[2 * p.w * p.c + ch] - pre[lo * p.c + ch] + pre[(lo + span - 2 * p.w) * p.c + ch] }
                out[(y * p.w + x) * p.c + ch] = Float((sum / Double(span)) * (1 - t) + mean[ch] * t)
            }
        }
    }
    p.px = out
}

func toRGB(_ p: Picture) -> Picture {
    let q = Picture(w: p.w, h: p.h, c: 3)
    for i in 0..<(p.w * p.h) { for k in 0..<3 { q.px[i * 3 + k] = p.px[i] } }
    return q
}

// MARK: - the game's layout

/// From a map laid out east to the right with its left edge at lon0, to the game's layout: column j of the result shows
/// longitude 360 * (0.25 - (j + 0.5) / w) (mirror, the game's way) or 360 * ((j + 0.5) / w) - 180 (not mirrored); rows
/// from the bottom (south) when flipRows.
func toGame(_ p: Picture, lon0: Double, mirror: Bool, flipRows: Bool) -> Picture {
    let q = Picture(w: p.w, h: p.h, c: p.c)
    for j in 0..<p.w {
        let u = (Double(j) + 0.5) / Double(p.w)
        let lon = mirror ? 360.0 * (0.25 - u) : 360.0 * u - 180.0
        var x = ((lon - lon0) / 360.0) * Double(p.w) - 0.5
        x = x - floor(x / Double(p.w)) * Double(p.w)
        let x0 = Int(floor(x)) % p.w, x1 = (x0 + 1) % p.w
        let f = Float(x - floor(x))
        for y in 0..<p.h {
            let ty = flipRows ? p.h - 1 - y : y
            for ch in 0..<p.c {
                let a = p.px[(y * p.w + x0) * p.c + ch], b = p.px[(y * p.w + x1) * p.c + ch]
                q.px[(ty * p.w + j) * p.c + ch] = a + (b - a) * f
            }
        }
    }
    return q
}


// MARK: - writing DDS

func ddsHeader(w: Int, h: Int, mips: Int, fourCC: String?, rgbBits: Int = 0, masks: [UInt32] = [0, 0, 0, 0], linearSize: Int) -> Data {
    var d = Data()
    func u32(_ v: UInt32) { var x = v.littleEndian; d.append(Data(bytes: &x, count: 4)) }
    d.append("DDS ".data(using: .ascii)!)
    u32(124)
    let flags: UInt32 = 0x1 | 0x2 | 0x4 | 0x1000 | (mips > 1 ? 0x20000 : 0) | (fourCC != nil ? 0x80000 : 0x8)
    u32(flags); u32(UInt32(h)); u32(UInt32(w)); u32(UInt32(linearSize)); u32(0); u32(UInt32(mips))
    for _ in 0..<11 { u32(0) }
    // pixel format
    u32(32)
    if let cc = fourCC {
        u32(0x4)
        d.append(cc.data(using: .ascii)!)
        u32(0); u32(0); u32(0); u32(0); u32(0)
    } else {
        u32(masks[3] != 0 ? 0x41 : 0x40); u32(0); u32(UInt32(rgbBits)); u32(masks[0]); u32(masks[1]); u32(masks[2]); u32(masks[3])
    }
    u32(0x1000 | (mips > 1 ? 0x400008 : 0)); u32(0); u32(0); u32(0); u32(0)
    return d
}

/// 16-bit heights as a DX10 DDS of DXGI_FORMAT_R16_UNORM (one level).
func writeR16(_ p: Picture, low: Float, high: Float, to path: String) {
    var d = ddsHeader(w: p.w, h: p.h, mips: 1, fourCC: "DX10", linearSize: p.w * 2)
    func u32(_ v: UInt32) { var x = v.littleEndian; d.append(Data(bytes: &x, count: 4)) }
    u32(56); u32(3); u32(0); u32(1); u32(0)   // R16_UNORM, a 2D texture, one of it
    var body = [UInt8](repeating: 0, count: p.w * p.h * 2)
    for i in 0..<(p.w * p.h) {
        let f = max(0, min(1, (p.px[i] - low) / (high - low)))
        let v = UInt16((f * 65535).rounded())
        body[2 * i] = UInt8(v & 0xFF); body[2 * i + 1] = UInt8(v >> 8)
    }
    d.append(contentsOf: body)
    try! d.write(to: URL(fileURLWithPath: path))
}

/// Mipmaps of an RGB(A) picture (each half the last, by averaging).
func mipChain(_ p: Picture) -> [Picture] {
    var out = [p]
    var cur = p
    while cur.w > 4 && cur.h > 4 {
        let n = Picture(w: cur.w / 2, h: cur.h / 2, c: cur.c)
        for y in 0..<n.h { for x in 0..<n.w { for ch in 0..<cur.c {
            let a = cur.px[((2 * y) * cur.w + 2 * x) * cur.c + ch] + cur.px[((2 * y) * cur.w + 2 * x + 1) * cur.c + ch]
            let b = cur.px[((2 * y + 1) * cur.w + 2 * x) * cur.c + ch] + cur.px[((2 * y + 1) * cur.w + 2 * x + 1) * cur.c + ch]
            n.px[(y * n.w + x) * n.c + ch] = (a + b) * 0.25
        } } }
        out.append(n)
        cur = n
    }
    return out
}

@inline(__always) func to565(_ r: Float, _ g: Float, _ b: Float) -> UInt16 {
    let R = UInt16(max(0, min(31, (r / 255 * 31).rounded()))), G = UInt16(max(0, min(63, (g / 255 * 63).rounded()))), B = UInt16(max(0, min(31, (b / 255 * 31).rounded())))
    return R << 11 | G << 5 | B
}
@inline(__always) func from565(_ v: UInt16) -> (Float, Float, Float) {
    let r = Float((v >> 11) & 31), g = Float((v >> 5) & 63), b = Float(v & 31)
    return (r * 255 / 31, g * 255 / 63, b * 255 / 31)
}

/// One 4x4 block of colour, as BC1 (four colours along the block's longest line).
func bc1Block(_ c: [(Float, Float, Float)]) -> [UInt8] {
    var mean = (Float(0), Float(0), Float(0))
    for p in c { mean.0 += p.0; mean.1 += p.1; mean.2 += p.2 }
    mean = (mean.0 / 16, mean.1 / 16, mean.2 / 16)
    // the longest line: power iteration on the colours' spread
    var cov = [Float](repeating: 0, count: 6)
    for p in c { let d = (p.0 - mean.0, p.1 - mean.1, p.2 - mean.2); cov[0] += d.0 * d.0; cov[1] += d.0 * d.1; cov[2] += d.0 * d.2; cov[3] += d.1 * d.1; cov[4] += d.1 * d.2; cov[5] += d.2 * d.2 }
    var v = (Float(1), Float(1), Float(1))
    for _ in 0..<6 {
        let n = (cov[0] * v.0 + cov[1] * v.1 + cov[2] * v.2, cov[1] * v.0 + cov[3] * v.1 + cov[4] * v.2, cov[2] * v.0 + cov[4] * v.1 + cov[5] * v.2)
        let l = sqrt(n.0 * n.0 + n.1 * n.1 + n.2 * n.2)
        if l < 1e-6 { break }
        v = (n.0 / l, n.1 / l, n.2 / l)
    }
    var lo: Float = .greatestFiniteMagnitude, hi: Float = -.greatestFiniteMagnitude
    for p in c { let t = (p.0 - mean.0) * v.0 + (p.1 - mean.1) * v.1 + (p.2 - mean.2) * v.2; lo = min(lo, t); hi = max(hi, t) }
    var e0 = to565(mean.0 + v.0 * hi, mean.1 + v.1 * hi, mean.2 + v.2 * hi)
    var e1 = to565(mean.0 + v.0 * lo, mean.1 + v.1 * lo, mean.2 + v.2 * lo)
    if e0 < e1 { swap(&e0, &e1) }
    var idx = [UInt8](repeating: 0, count: 16)
    if e0 != e1 {
        let a = from565(e0), b = from565(e1)
        let pal = [a, b, ((2 * a.0 + b.0) / 3, (2 * a.1 + b.1) / 3, (2 * a.2 + b.2) / 3), ((a.0 + 2 * b.0) / 3, (a.1 + 2 * b.1) / 3, (a.2 + 2 * b.2) / 3)]
        for (i, p) in c.enumerated() {
            var best = 0; var bd = Float.greatestFiniteMagnitude
            for (k, q) in pal.enumerated() { let d = (p.0 - q.0) * (p.0 - q.0) + (p.1 - q.1) * (p.1 - q.1) + (p.2 - q.2) * (p.2 - q.2); if d < bd { bd = d; best = k } }
            idx[i] = UInt8(best)
        }
    }
    var bits: UInt32 = 0
    for i in 0..<16 { bits |= UInt32(idx[i]) << (2 * i) }
    return [UInt8(e0 & 0xFF), UInt8(e0 >> 8), UInt8(e1 & 0xFF), UInt8(e1 >> 8), UInt8(bits & 0xFF), UInt8((bits >> 8) & 0xFF), UInt8((bits >> 16) & 0xFF), UInt8(bits >> 24)]
}

/// One 4x4 block of a single channel, as BC4 / DXT5's alpha (eight values between the block's least and most).
func alphaBlock(_ a: [Float]) -> [UInt8] {
    let lo = a.min()!, hi = a.max()!
    let a0 = UInt8(max(0, min(255, hi.rounded()))), a1 = UInt8(max(0, min(255, lo.rounded())))
    var out: [UInt8] = [a0, a1]
    var bits: UInt64 = 0
    if a0 > a1 {
        let pal = (0..<8).map { k -> Float in
            switch k { case 0: return Float(a0); case 1: return Float(a1); default: return (Float(8 - k) * Float(a0) + Float(k - 1) * Float(a1)) / 7 }
        }
        for (i, v) in a.enumerated() {
            var best = 0; var bd = Float.greatestFiniteMagnitude
            for (k, q) in pal.enumerated() { let d = abs(v - q); if d < bd { bd = d; best = k } }
            bits |= UInt64(best) << UInt64(3 * i)
        }
    }
    for k in 0..<6 { out.append(UInt8((bits >> UInt64(8 * k)) & 0xFF)) }
    return out
}

func blocks(_ p: Picture, _ each: (_ bx: Int, _ by: Int) -> [UInt8]) -> [UInt8] {
    var out: [UInt8] = []
    out.reserveCapacity(max(1, p.w / 4) * max(1, p.h / 4) * 16)
    for by in 0..<max(1, p.h / 4) { for bx in 0..<max(1, p.w / 4) { out.append(contentsOf: each(bx, by)) } }
    return out
}

func writeBC1(_ p: Picture, mips: Bool, to path: String) {
    let chain = mips ? mipChain(p) : [p]
    var d = ddsHeader(w: p.w, h: p.h, mips: chain.count, fourCC: "DXT1", linearSize: max(1, p.w / 4) * max(1, p.h / 4) * 8)
    for m in chain {
        d.append(contentsOf: blocks(m) { bx, by in
            var c: [(Float, Float, Float)] = []
            for y in 0..<4 { for x in 0..<4 {
                let sx = min(m.w - 1, bx * 4 + x), sy = min(m.h - 1, by * 4 + y)
                let o = (sy * m.w + sx) * 3
                c.append((m.px[o], m.px[o + 1], m.px[o + 2]))
            } }
            return bc1Block(c)
        })
    }
    try! d.write(to: URL(fileURLWithPath: path))
}

/// A normal map as DXT5: x in alpha, y in green (red and blue a flat grey), as Unity's UnpackNormal reads one.
func writeNormalsDXT5(_ n: Picture, mips: Bool, to path: String) {
    let chain = mips ? mipChain(n) : [n]
    var d = ddsHeader(w: n.w, h: n.h, mips: chain.count, fourCC: "DXT5", linearSize: max(1, n.w / 4) * max(1, n.h / 4) * 16)
    for m in chain {
        d.append(contentsOf: blocks(m) { bx, by in
            var a: [Float] = [], c: [(Float, Float, Float)] = []
            for y in 0..<4 { for x in 0..<4 {
                let sx = min(m.w - 1, bx * 4 + x), sy = min(m.h - 1, by * 4 + y)
                let o = (sy * m.w + sx) * 3
                a.append(m.px[o])                      // x
                c.append((128, m.px[o + 1], 128))       // y in green
            } }
            return alphaBlock(a) + bc1Block(c)
        })
    }
    try! d.write(to: URL(fileURLWithPath: path))
}

// MARK: - the jobs

func heights(_ j: Job) -> Picture {
    let scale = Float(j.scale ?? 1), add = Float(j.add ?? 0)
    return resampled(rows(j, grey: true), w: j.width, h: j.height, channels: 1, nodata: j.nodata.map(Float.init),
                     dropLast: j.dropLast ?? false) { $0 * scale + add }
}

func run(_ j: Job) {
    let t0 = Date()
    let mirror = j.mirror ?? true, flip = j.flipRows ?? true
    let lon0: Double = j.lon0 ?? geoLeftEdge(j.in) ?? -180
    if j.lon0 == nil { print(String(format: "%@: its left edge is at longitude %.4f", (j.in as NSString).lastPathComponent, lon0)) }
    switch j.kind {
    case "height":
        let p = toGame(heights(j), lon0: lon0, mirror: mirror, flipRows: flip)
        var lo = Float.greatestFiniteMagnitude, hi = -Float.greatestFiniteMagnitude
        for v in p.px { lo = min(lo, v); hi = max(hi, v) }
        let low = Float(j.low ?? Double(lo)), high = Float(j.high ?? Double(hi))
        writeR16(p, low: low, high: high, to: j.out)
        print(String(format: "%@: %dx%d heights %.1f..%.1f m; offset = %.1f, deformity = %.1f (%.2f s)", j.out, p.w, p.h, lo, hi, low, high - low, Date().timeIntervalSince(t0)))
    case "colour":
        let src = rows(j, grey: j.grey ?? false)
        let per: Float = j.deep ?? false ? 255.0 / 65535.0 : 1
        var p = resampled(src, w: j.width, h: j.height, channels: (j.grey ?? false) ? 1 : 3, nodata: j.nodata.map(Float.init),
                          dropLast: j.dropLast ?? false) { $0 * per }
        if p.c == 1 { p = toRGB(p) }
        let tint = j.tint ?? [1, 1, 1], g = Float(j.gamma ?? 1)
        for i in 0..<(p.w * p.h) { for k in 0..<3 {
            var v = p.px[i * 3 + k] / 255
            if g != 1 { v = pow(max(0, v), g) }
            p.px[i * 3 + k] = max(0, min(255, v * Float(tint[k]) * 255))
        } }
        p = toGame(p, lon0: lon0, mirror: mirror, flipRows: flip)
        writeBC1(p, mips: j.mips ?? true, to: j.out)
        print(String(format: "%@: %dx%d colour (%.2f s)", j.out, p.w, p.h, Date().timeIntervalSince(t0)))
    case "normals":
        let h = toGame(heights(j), lon0: lon0, mirror: mirror, flipRows: flip)
        if let fl = j.floorAt { let f = Float(fl); for i in 0..<h.px.count where h.px[i] < f { h.px[i] = f } }
        let R = j.radius ?? 1, k = Float(j.strength ?? 1)
        let n = Picture(w: h.w, h: h.h, c: 3)
        // slopes in metres per metre: across a column is 2 pi R cos(lat) / w, a row pi R / h
        for y in 0..<h.h {
            let lat = (Double(y) + 0.5) / Double(h.h) * Double.pi - Double.pi / 2   // rows from the south when flipped
            let latRow = flip ? lat : -lat
            let dx = Float(2 * Double.pi * R * max(0.01, cos(latRow)) / Double(h.w)), dy = Float(Double.pi * R / Double(h.h))
            for x in 0..<h.w {
                let l = h.px[y * h.w + (x + h.w - 1) % h.w], r = h.px[y * h.w + (x + 1) % h.w]
                let dn = h.px[max(0, y - 1) * h.w + x], up = h.px[min(h.h - 1, y + 1) * h.w + x]
                var sx = (r - l) / (2 * dx) * k, sy = (up - dn) / (2 * dy) * k
                if mirror { sx = -sx }          // (the columns run west)
                if !flip { sy = -sy }
                let len = sqrt(sx * sx + sy * sy + 1)
                let nx = -sx / len, ny = -sy / len
                n.px[(y * h.w + x) * 3] = (nx * 0.5 + 0.5) * 255
                n.px[(y * h.w + x) * 3 + 1] = (ny * 0.5 + 0.5) * 255
                n.px[(y * h.w + x) * 3 + 2] = (1 / len * 0.5 + 0.5) * 255
            }
        }
        writeNormalsDXT5(n, mips: j.mips ?? true, to: j.out)
        print(String(format: "%@: %dx%d normals (%.2f s)", j.out, n.w, n.h, Date().timeIntervalSince(t0)))
    default:
        fail("a job of kind \(j.kind)?")
    }
}

let args = CommandLine.arguments
guard args.count > 1, let data = FileManager.default.contents(atPath: args[1]) else { fail("usage: maps jobs.json") }
let jobs = try! JSONDecoder().decode([Job].self, from: data)
for j in jobs { run(j) }
