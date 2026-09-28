import Foundation
import Capacitor
import StoreKit

/// YardScout Pro subscription via StoreKit 2 — no third-party IAP service.
/// StoreKit 2 cryptographically verifies transactions on-device, which is the
/// right level of enforcement for an app whose Pro gate is client-side anyway.
///
/// JS surface (window.Capacitor.Plugins.Purchases):
///   getProduct({ productId })  -> { available, price?, displayName?, period? }
///   purchase({ productId })    -> { entitled }
///   restore()                  -> { entitled }
///   isEntitled({ productId })  -> { entitled }
@objc(PurchasesPlugin)
public class PurchasesPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "PurchasesPlugin"
    public let jsName = "Purchases"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "getProduct", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "purchase", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "restore", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "isEntitled", returnType: CAPPluginReturnPromise),
    ]

    private func productId(from call: CAPPluginCall) -> String {
        return call.getString("productId") ?? "yardscout_pro_monthly"
    }

    @objc func getProduct(_ call: CAPPluginCall) {
        let id = productId(from: call)
        Task {
            do {
                guard let product = try await Product.products(for: [id]).first else {
                    call.resolve(["available": false])
                    return
                }
                var out: [String: Any] = [
                    "available": true,
                    "price": product.displayPrice,
                    "displayName": product.displayName,
                ]
                if let sub = product.subscription {
                    out["period"] = "\(sub.subscriptionPeriod.value) \(sub.subscriptionPeriod.unit)"
                }
                call.resolve(out)
            } catch {
                call.resolve(["available": false, "error": error.localizedDescription])
            }
        }
    }

    @objc func purchase(_ call: CAPPluginCall) {
        let id = productId(from: call)
        Task {
            do {
                guard let product = try await Product.products(for: [id]).first else {
                    call.reject("Product not available.")
                    return
                }
                let result = try await product.purchase()
                switch result {
                case .success(let verification):
                    switch verification {
                    case .verified(let transaction):
                        await transaction.finish()
                        call.resolve(["entitled": true])
                    case .unverified:
                        call.reject("Purchase could not be verified.")
                    }
                case .userCancelled:
                    call.resolve(["entitled": false, "cancelled": true])
                case .pending:
                    // Ask-to-buy etc. — entitlement arrives later; the app
                    // re-checks isEntitled on every launch.
                    call.resolve(["entitled": false, "pending": true])
                @unknown default:
                    call.resolve(["entitled": false])
                }
            } catch {
                call.reject(error.localizedDescription)
            }
        }
    }

    @objc func restore(_ call: CAPPluginCall) {
        let id = productId(from: call)
        Task {
            // AppStore.sync() forces a refresh from the App Store (sign-in UI
            // may appear); then re-derive entitlement from current state.
            try? await AppStore.sync()
            let entitled = await Self.checkEntitled(productId: id)
            call.resolve(["entitled": entitled])
        }
    }

    @objc func isEntitled(_ call: CAPPluginCall) {
        let id = productId(from: call)
        Task {
            let entitled = await Self.checkEntitled(productId: id)
            call.resolve(["entitled": entitled])
        }
    }

    static func checkEntitled(productId: String) async -> Bool {
        for await entitlement in Transaction.currentEntitlements {
            if case .verified(let transaction) = entitlement,
               transaction.productID == productId,
               transaction.revocationDate == nil {
                return true
            }
        }
        return false
    }
}
