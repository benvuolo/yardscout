package com.benvuolo.yardscout;

import android.app.Activity;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.google.android.play.core.review.ReviewInfo;
import com.google.android.play.core.review.ReviewManager;
import com.google.android.play.core.review.ReviewManagerFactory;

/**
 * Google Play in-app review — the Android twin of ios/App/App/ReviewPlugin.swift.
 * Play shows its rating card inside the app (no store trip) and applies its
 * own quota, so like iOS the result only says the system was asked.
 * docs/app.js (maybeAskForReview) decides when.
 *
 *   requestReview() -> { requested: boolean }
 */
@CapacitorPlugin(name = "Review")
public class ReviewPlugin extends Plugin {

    @PluginMethod
    public void requestReview(PluginCall call) {
        final Activity activity = getActivity();
        if (activity == null) { resolve(call, false); return; }
        final ReviewManager manager = ReviewManagerFactory.create(activity);
        manager.requestReviewFlow().addOnCompleteListener(task -> {
            if (!task.isSuccessful() || task.getResult() == null) { resolve(call, false); return; }
            ReviewInfo info = task.getResult();
            manager.launchReviewFlow(activity, info).addOnCompleteListener(flow -> resolve(call, true));
        });
    }

    private void resolve(PluginCall call, boolean requested) {
        JSObject r = new JSObject();
        r.put("requested", requested);
        call.resolve(r);
    }
}
