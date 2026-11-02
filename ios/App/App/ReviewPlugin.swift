import Foundation
import Capacitor
import StoreKit

/// In-app rating sheet. Apple shows its one-tap stars sheet inside the app
/// (no store trip) at most three times per 365 days per user, and may decide
/// not to show it at all — so requestReview() resolves { shown: true } only
/// meaning "asked the system"; whether a sheet appeared is up to StoreKit.
/// docs/app.js decides WHEN to ask (after a real win, never on launch or
/// near the paywall) — see maybeAskForReview there.
///
/// JS surface (window.Capacitor.Plugins.Review):
///   requestReview() -> { requested: Bool }
@objc(ReviewPlugin)
public class ReviewPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "ReviewPlugin"
    public let jsName = "Review"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "requestReview", returnType: CAPPluginReturnPromise),
    ]

    @objc func requestReview(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            let scene = UIApplication.shared.connectedScenes
                .compactMap { $0 as? UIWindowScene }
                .first { $0.activationState == .foregroundActive }
                ?? UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first
            guard let scene = scene else {
                call.resolve(["requested": false])
                return
            }
            if #available(iOS 16.0, *) {
                AppStore.requestReview(in: scene)
            } else {
                SKStoreReviewController.requestReview(in: scene)
            }
            call.resolve(["requested": true])
        }
    }
}
