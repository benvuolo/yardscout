import UIKit
import Capacitor

/// Registers the in-app plugins (Main.storyboard points here instead of the
/// stock CAPBridgeViewController).
class MainViewController: CAPBridgeViewController {
    override open func capacitorDidLoad() {
        bridge?.registerPluginInstance(PurchasesPlugin())
    }
}
