// cursorprobe - read-only: which cursor macOS is showing, and why, sampled every 50 ms.
//
// Build: swiftc -O -o build/cursorprobe tools/cursorprobe.swift   (scripts/cursor-test.sh does it)
// Run:   build/cursorprobe <seconds> [label]
//
// Per sample: the system-wide cursor (NSCursor.currentSystem: size in points, pixels, hot spot),
// WindowServer's software-cursor window if it is drawing one ("[Cursor]" in the window list, present
// only while the hardware cursor is off), the frontmost app, and the window under the pointer by the
// same call winemac uses to route mouse moves (+[NSWindow windowNumberAtPoint:...], cocoa_app.m:1369).
// Prints every change and a summary. It has no window, takes no focus and posts no events.
import AppKit

let secs = CommandLine.arguments.count > 1 ? Double(CommandLine.arguments[1]) ?? 10 : 10
let label = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "probe"
_ = NSApplication.shared
NSApp.setActivationPolicy(.prohibited)

func windows() -> [[String: Any]] {
    (CGWindowListCopyWindowInfo(.optionOnScreenOnly, kCGNullWindowID) as? [[String: Any]]) ?? []
}

var last = "", counts: [String: Int] = [:], samples = 0
let t0 = Date(), H = NSScreen.screens[0].frame.height
while Date().timeIntervalSince(t0) < secs {
    autoreleasepool {
        let list = windows()
        var byNum: [Int: [String: Any]] = [:]
        var swCursor = "hw"
        for w in list {
            let n = w[kCGWindowNumber as String] as? Int ?? 0
            byNum[n] = w
            if (w[kCGWindowName as String] as? String) == "Cursor",
               let b = w[kCGWindowBounds as String] as? [String: Double] {
                swCursor = "sw \(Int(b["Width"] ?? 0))x\(Int(b["Height"] ?? 0))"
            }
        }
        let p = CGEvent(source: nil)?.location ?? .zero
        let n = NSWindow.windowNumber(at: NSPoint(x: p.x, y: H - p.y), belowWindowWithWindowNumber: 0)
        let under = byNum[n].map { "\($0[kCGWindowOwnerName as String] ?? "?") L\($0[kCGWindowLayer as String] ?? 0)" } ?? "none"
        let front = NSWorkspace.shared.frontmostApplication?.localizedName ?? "?"
        var cur = "?"
        if let c = NSCursor.currentSystem {
            let px = c.image.representations.first?.pixelsWide ?? 0
            cur = "\(Int(c.image.size.width))x\(Int(c.image.size.height))pt/\(px)px hot \(Int(c.hotSpot.x)),\(Int(c.hotSpot.y))"
        }
        let state = "cursor \(cur) | \(swCursor) | front \(front) | under \(under)"
        samples += 1
        counts[state, default: 0] += 1
        if state != last {
            print(String(format: "%@ %6.2f  ", label, Date().timeIntervalSince(t0)) + state)
            last = state
        }
    }
    usleep(50_000)
}
print("\(label) summary over \(samples) samples:")
for (k, v) in counts.sorted(by: { $0.value > $1.value }) {
    print(String(format: "  %5.1f%%  ", 100.0 * Double(v) / Double(max(samples, 1))) + k)
}
