package com.benvuolo.yardscout;

import android.app.Activity;

import com.android.billingclient.api.AcknowledgePurchaseParams;
import com.android.billingclient.api.BillingClient;
import com.android.billingclient.api.BillingClientStateListener;
import com.android.billingclient.api.BillingFlowParams;
import com.android.billingclient.api.BillingResult;
import com.android.billingclient.api.PendingPurchasesParams;
import com.android.billingclient.api.ProductDetails;
import com.android.billingclient.api.Purchase;
import com.android.billingclient.api.PurchasesUpdatedListener;
import com.android.billingclient.api.QueryProductDetailsParams;
import com.android.billingclient.api.QueryProductDetailsResult;
import com.android.billingclient.api.QueryPurchasesParams;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.util.Collections;
import java.util.List;

/**
 * YardScout Pro subscription via Google Play Billing — the Android twin of
 * ios/App/App/PurchasesPlugin.swift (StoreKit 2). Same JS surface, so
 * docs/app.js needs no platform branching for purchases:
 *
 *   getProduct({ productId })  -> { available, price?, displayName?, period?,
 *                                   introPrice?, introPeriod?, introCycles? }
 *   purchase({ productId })    -> { entitled } (+ cancelled / pending flags)
 *   restore()                  -> { entitled }
 *   isEntitled({ productId })  -> { entitled }
 *   getPurchaseToken({ productId }) -> { entitled, purchaseToken?, orderId? }
 *       (the Play twin of iOS getTransactionJws — hands the JS layer the
 *        proof-of-purchase it POSTs to /api/ent/verify-android to link an
 *        email; the server re-verifies with Google, never trusts the client)
 *
 * Entitlement is re-derived from Play's purchase cache on every launch (same
 * strategy as iOS: renewals extend, cancellations lapse at period end, refunds
 * revoke). Connection failures REJECT rather than resolving entitled:false so
 * the JS layer keeps the last known Pro state while offline — identical to the
 * iOS behavior where StoreKit's local cache answers offline.
 *
 * Play Billing requires purchases to be acknowledged within 3 days or they
 * auto-refund; this plugin acknowledges inline after a successful purchase AND
 * sweeps unacknowledged purchases during every entitlement check as a safety
 * net (covers "purchase succeeded but the ack network call died" and
 * pending->purchased transitions that complete while the app is closed).
 */
@CapacitorPlugin(name = "Purchases")
public class PurchasesPlugin extends Plugin implements PurchasesUpdatedListener {

    private static final String DEFAULT_PRODUCT_ID = "yardscout_pro_monthly";

    private BillingClient billingClient;
    /** The in-flight purchase() call, resolved from onPurchasesUpdated. */
    private PluginCall purchaseCall;
    private String purchaseProductId;

    @Override
    public void load() {
        billingClient = BillingClient.newBuilder(getContext())
            .setListener(this)
            .enablePendingPurchases(
                PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
            .build();
    }

    private String productId(PluginCall call) {
        String id = call.getString("productId");
        return id != null ? id : DEFAULT_PRODUCT_ID;
    }

    /** Run `onReady` with a connected billing client, or fail the call. */
    private void withConnection(PluginCall call, Runnable onReady) {
        if (billingClient.isReady()) {
            onReady.run();
            return;
        }
        billingClient.startConnection(new BillingClientStateListener() {
            @Override
            public void onBillingSetupFinished(BillingResult result) {
                if (result.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                    onReady.run();
                } else {
                    call.reject(billingMessage(result));
                }
            }

            @Override
            public void onBillingServiceDisconnected() {
                // Next plugin call will reconnect via startConnection.
            }
        });
    }

    private static String billingMessage(BillingResult result) {
        switch (result.getResponseCode()) {
            case BillingClient.BillingResponseCode.BILLING_UNAVAILABLE:
            case BillingClient.BillingResponseCode.SERVICE_UNAVAILABLE:
            case BillingClient.BillingResponseCode.SERVICE_DISCONNECTED:
                return "Google Play billing isn\u2019t available on this device right now.";
            case BillingClient.BillingResponseCode.NETWORK_ERROR:
                return "Can\u2019t reach Google Play \u2014 check your connection and try again.";
            default:
                String dbg = result.getDebugMessage();
                return (dbg != null && !dbg.isEmpty()) ? dbg : "Google Play billing error.";
        }
    }

    private void queryProduct(String id, ProductQueryCallback cb) {
        QueryProductDetailsParams params = QueryProductDetailsParams.newBuilder()
            .setProductList(Collections.singletonList(
                QueryProductDetailsParams.Product.newBuilder()
                    .setProductId(id)
                    .setProductType(BillingClient.ProductType.SUBS)
                    .build()))
            .build();
        // Billing 8.x: the listener receives a QueryProductDetailsResult
        // (products + unfetched list) instead of a bare List<ProductDetails>.
        billingClient.queryProductDetailsAsync(params, (result, detailsResult) -> {
            List<ProductDetails> products =
                detailsResult != null ? detailsResult.getProductDetailsList() : null;
            if (result.getResponseCode() == BillingClient.BillingResponseCode.OK
                    && products != null && !products.isEmpty()) {
                cb.onResult(products.get(0), null);
            } else {
                cb.onResult(null, billingMessage(result));
            }
        });
    }

    private interface ProductQueryCallback {
        void onResult(ProductDetails product, String error);
    }

    /** Base-plan recurring price lives in the LAST pricing phase (earlier
     *  phases are intro offers / free trials, none configured today). */
    private static ProductDetails.PricingPhase basePricingPhase(ProductDetails product) {
        ProductDetails.SubscriptionOfferDetails o = bestOffer(product);
        if (o == null) return null;
        List<ProductDetails.PricingPhase> phases = o.getPricingPhases().getPricingPhaseList();
        return phases.isEmpty() ? null : phases.get(phases.size() - 1);
    }

    /**
     * The offer to show and buy (2026-10-30, intro price). Play lists only the
     * offers this user is ELIGIBLE for, in no guaranteed order — the base plan
     * (offerId null) plus e.g. a "new customer" intro offer. offers.get(0) could
     * be the base plan and charge a first-timer full price. Prefer the offer
     * whose first phase is cheapest; ties go to the base plan.
     */
    private static ProductDetails.SubscriptionOfferDetails bestOffer(ProductDetails product) {
        List<ProductDetails.SubscriptionOfferDetails> offers = product.getSubscriptionOfferDetails();
        if (offers == null || offers.isEmpty()) return null;
        ProductDetails.SubscriptionOfferDetails best = null;
        long bestMicros = Long.MAX_VALUE;
        for (ProductDetails.SubscriptionOfferDetails o : offers) {
            List<ProductDetails.PricingPhase> phases = o.getPricingPhases().getPricingPhaseList();
            if (phases.isEmpty()) continue;
            long first = phases.get(0).getPriceAmountMicros();
            boolean better = first < bestMicros || (first == bestMicros && o.getOfferId() == null);
            if (best == null || better) { best = o; bestMicros = first; }
        }
        return best != null ? best : offers.get(0);
    }

    private static String humanPeriod(String iso) {
        if (iso == null) return null;
        switch (iso) {
            case "P1M": return "1 month";
            case "P1Y": return "1 year";
            case "P1W": return "1 week";
            default: return iso;
        }
    }

    @PluginMethod
    public void getProduct(PluginCall call) {
        String id = productId(call);
        withConnection(call, () -> queryProduct(id, (product, error) -> {
            JSObject out = new JSObject();
            if (product == null) {
                out.put("available", false);
                if (error != null) out.put("error", error);
                call.resolve(out);
                return;
            }
            out.put("available", true);
            out.put("displayName", product.getName());
            ProductDetails.PricingPhase phase = basePricingPhase(product);
            if (phase != null) {
                out.put("price", phase.getFormattedPrice());
                String period = humanPeriod(phase.getBillingPeriod());
                if (period != null) out.put("period", period);
            }
            // Intro price (same keys as the iOS plugin): the best offer's
            // first phase, when it's cheaper than the recurring price.
            ProductDetails.SubscriptionOfferDetails best = bestOffer(product);
            if (best != null && phase != null) {
                List<ProductDetails.PricingPhase> phases = best.getPricingPhases().getPricingPhaseList();
                ProductDetails.PricingPhase first = phases.get(0);
                if (phases.size() > 1 && first.getPriceAmountMicros() < phase.getPriceAmountMicros()) {
                    out.put("introPrice", first.getPriceAmountMicros() == 0 ? "Free" : first.getFormattedPrice());
                    String ip = humanPeriod(first.getBillingPeriod());
                    if (ip != null) out.put("introPeriod", ip);
                    out.put("introCycles", Math.max(1, first.getBillingCycleCount()));
                }
            }
            call.resolve(out);
        }));
    }

    @PluginMethod
    public void purchase(PluginCall call) {
        String id = productId(call);
        withConnection(call, () -> queryProduct(id, (product, error) -> {
            if (product == null) {
                call.reject(error != null ? error : "Product not available.");
                return;
            }
            ProductDetails.SubscriptionOfferDetails offer = bestOffer(product);
            if (offer == null) {
                call.reject("Product not available.");
                return;
            }
            Activity activity = getActivity();
            if (activity == null) {
                call.reject("Purchase failed.");
                return;
            }
            BillingFlowParams flowParams = BillingFlowParams.newBuilder()
                .setProductDetailsParamsList(Collections.singletonList(
                    BillingFlowParams.ProductDetailsParams.newBuilder()
                        .setProductDetails(product)
                        .setOfferToken(offer.getOfferToken())
                        .build()))
                .build();
            purchaseCall = call;
            purchaseProductId = id;
            activity.runOnUiThread(() -> {
                BillingResult launch = billingClient.launchBillingFlow(activity, flowParams);
                if (launch.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                    purchaseCall = null;
                    purchaseProductId = null;
                    call.reject(billingMessage(launch));
                }
            });
        }));
    }

    /** Result of the Play purchase sheet (success, cancel, pending, error). */
    @Override
    public void onPurchasesUpdated(BillingResult result, List<Purchase> purchases) {
        PluginCall call = purchaseCall;
        String id = purchaseProductId != null ? purchaseProductId : DEFAULT_PRODUCT_ID;
        purchaseCall = null;
        purchaseProductId = null;
        if (call == null) return; // e.g. out-of-app renewal notification

        if (result.getResponseCode() == BillingClient.BillingResponseCode.USER_CANCELED) {
            JSObject out = new JSObject();
            out.put("entitled", false);
            out.put("cancelled", true);
            call.resolve(out);
            return;
        }
        if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
            call.reject(billingMessage(result));
            return;
        }
        Purchase match = null;
        if (purchases != null) {
            for (Purchase p : purchases) {
                if (p.getProducts().contains(id)) { match = p; break; }
            }
        }
        JSObject out = new JSObject();
        if (match != null && match.getPurchaseState() == Purchase.PurchaseState.PURCHASED) {
            acknowledgeIfNeeded(match);
            out.put("entitled", true);
        } else if (match != null && match.getPurchaseState() == Purchase.PurchaseState.PENDING) {
            // Slow payment method — entitlement arrives later; the app
            // re-checks isEntitled on every launch (mirrors iOS ask-to-buy).
            out.put("entitled", false);
            out.put("pending", true);
        } else {
            out.put("entitled", false);
        }
        call.resolve(out);
    }

    private void acknowledgeIfNeeded(Purchase purchase) {
        if (purchase.isAcknowledged()) return;
        billingClient.acknowledgePurchase(
            AcknowledgePurchaseParams.newBuilder()
                .setPurchaseToken(purchase.getPurchaseToken())
                .build(),
            ackResult -> { /* retried by the entitlement-check sweep if it failed */ });
    }

    /** Shared by isEntitled + restore: re-derive entitlement from Play's
     *  purchase records, acknowledging anything that still needs it. */
    private void checkEntitled(PluginCall call, String id) {
        billingClient.queryPurchasesAsync(
            QueryPurchasesParams.newBuilder()
                .setProductType(BillingClient.ProductType.SUBS)
                .build(),
            (result, purchases) -> {
                if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                    // Reject so the JS catch keeps the last known Pro state
                    // (offline / Play outage), matching iOS offline behavior.
                    call.reject(billingMessage(result));
                    return;
                }
                boolean entitled = false;
                for (Purchase p : purchases) {
                    if (p.getProducts().contains(id)
                            && p.getPurchaseState() == Purchase.PurchaseState.PURCHASED) {
                        entitled = true;
                        acknowledgeIfNeeded(p);
                    }
                }
                JSObject out = new JSObject();
                out.put("entitled", entitled);
                call.resolve(out);
            });
    }

    @PluginMethod
    public void isEntitled(PluginCall call) {
        String id = productId(call);
        withConnection(call, () -> checkEntitled(call, id));
    }

    @PluginMethod
    public void restore(PluginCall call) {
        // queryPurchasesAsync reads Play's cache for the signed-in account,
        // which Play keeps synced — the Android analog of AppStore.sync().
        String id = productId(call);
        withConnection(call, () -> checkEntitled(call, id));
    }

    /** Proof-of-purchase for the cross-device email link (the Android analog
     *  of getTransactionJws on iOS): the current purchase token for the Pro
     *  subscription, straight from Play's purchase records. The token is only
     *  useful server-side — the entitlement API re-verifies it with Google's
     *  Play Developer API before linking anything. */
    @PluginMethod
    public void getPurchaseToken(PluginCall call) {
        String id = productId(call);
        withConnection(call, () -> billingClient.queryPurchasesAsync(
            QueryPurchasesParams.newBuilder()
                .setProductType(BillingClient.ProductType.SUBS)
                .build(),
            (result, purchases) -> {
                if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
                    call.reject(billingMessage(result));
                    return;
                }
                Purchase match = null;
                for (Purchase p : purchases) {
                    if (p.getProducts().contains(id)
                            && p.getPurchaseState() == Purchase.PurchaseState.PURCHASED) {
                        match = p;
                        break;
                    }
                }
                JSObject out = new JSObject();
                if (match == null) {
                    out.put("entitled", false);
                    call.resolve(out);
                    return;
                }
                acknowledgeIfNeeded(match);
                out.put("entitled", true);
                out.put("purchaseToken", match.getPurchaseToken());
                String orderId = match.getOrderId();
                if (orderId != null) out.put("orderId", orderId);
                call.resolve(out);
            }));
    }
}
