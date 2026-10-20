package com.benvuolo.yardscout;

import android.os.Bundle;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        // Custom plugins must be registered BEFORE super.onCreate — the Android
        // analog of iOS gotcha #2 (MainViewController.capacitorDidLoad).
        registerPlugin(PurchasesPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
