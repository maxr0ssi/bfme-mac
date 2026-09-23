import CoreGraphics
import Foundation
let opts: CGWindowListOption = [.optionAll]
let list = CGWindowListCopyWindowInfo(opts, kCGNullWindowID) as! [[String: Any]]
for w in list {
    let owner = w["kCGWindowOwnerName"] as? String ?? "?"
    let name = w["kCGWindowName"] as? String ?? ""
    let id = w["kCGWindowNumber"] as? Int ?? 0
    let layer = w["kCGWindowLayer"] as? Int ?? 0
    let onscreen = w["kCGWindowIsOnscreen"] as? Bool ?? false
    let b = w["kCGWindowBounds"] as? [String: Any] ?? [:]
    if owner.lowercased().contains("wine") || owner.lowercased().contains("game") || owner.lowercased().contains("lotr") || name.lowercased().contains("lord") || name.lowercased().contains("bfme") {
        print("id=\(id) owner=\(owner) name=\(name) layer=\(layer) onscreen=\(onscreen) bounds=\(b)")
    }
}
