# Releasing YardScout to the stores from GitHub Actions

Two manual workflows build the native apps from the current `docs/` shell
and upload them, so a release is one "Run workflow" click (or one `gh
workflow run`) instead of a Mac session:

| Workflow | Does | Where it lands |
|---|---|---|
| **Release Android** (`.github/workflows/release-android.yml`) | stage → `cap sync android` → bump `versionCode`/`versionName` → signed `bundleRelease` → upload | Play **internal** track by default, **production** on request (status *completed*, release notes from the input) |
| **Release iOS** (`.github/workflows/release-ios.yml`) | stage → `cap sync ios` → bump `MARKETING_VERSION`/`CURRENT_PROJECT_VERSION` → archive → upload | **TestFlight**; with `submit=true` it also creates the App Store version, sets What's New, attaches the build and submits for review (auto-release on approval) |

Both commit the version bump back to `main`, so source always matches the
store. The web app needs nothing: pushing `main` deploys it.

```bash
gh workflow run release-android.yml -f version_name=1.10 -f track=internal -f notes="..."
gh workflow run release-ios.yml -f marketing_version=1.10 -f notes="..." -f submit=false
```

## One-time setup — repository secrets

GitHub → the repo → Settings → Secrets and variables → Actions → *New
repository secret*. Nothing here is ever printed by the workflows.

### Android

| Secret | Value | Where it comes from |
|---|---|---|
| `ANDROID_KEYSTORE_BASE64` | the upload keystore, base64 | on the Mac: `base64 -i ~/yardscout-android/<keystore>.jks \| pbcopy` (the path is in `~/yardscout-android/keystore.properties` → `storeFile`) |
| `ANDROID_KEYSTORE_PASSWORD` | `storePassword` | `~/yardscout-android/keystore.properties` |
| `ANDROID_KEY_ALIAS` | `keyAlias` | same file |
| `ANDROID_KEY_PASSWORD` | `keyPassword` | same file |
| `PLAY_SERVICE_ACCOUNT_JSON` | the whole JSON key file of a Google service account | see below |

**Play service account.** The backend already uses one to verify purchases
(`backend/site-proxy/wrangler.toml` → `GOOGLE_SA_EMAIL`). Reuse it:

1. Play Console → *Users and permissions* → *Invite new users* → enter the
   service-account email → under *App permissions* pick YardScout and grant
   **Release to production, exclude devices, and use Play App Signing** and
   **Manage testing tracks and edit tester lists** (plus *View app
   information* which comes along). Send invite — it's accepted
   automatically for service accounts.
2. Its JSON key: Google Cloud Console → IAM & Admin → Service Accounts →
   that account → Keys → *Add key* → JSON (if the original key file isn't
   saved anywhere). Paste the file's full contents into the secret.

### iOS

| Secret | Value | Where it comes from |
|---|---|---|
| `ASC_KEY_ID` | e.g. `ABC123DEF4` | App Store Connect → *Users and Access* → *Integrations* → *App Store Connect API* → **Team Keys** → *Generate API Key*, name "GitHub Actions", access **App Manager** |
| `ASC_ISSUER_ID` | UUID shown at the top of that page | same page |
| `ASC_API_KEY_P8` | contents of the downloaded `AuthKey_<KEY_ID>.p8` | downloadable **once**, right after creating the key — `cat AuthKey_*.p8 \| pbcopy` |
| `IOS_DIST_CERT_P12_BASE64` | the *Apple Distribution* certificate **with its private key**, exported as `.p12`, base64 | Keychain Access on the Mac that has built the app → *My Certificates* → "Apple Distribution: BENJAMIN ALEXANDER VUOLO (G23Z9MSBUG)" → right-click → *Export* → .p12 with a password → `base64 -i cert.p12 \| pbcopy` |
| `IOS_DIST_CERT_P12_PASSWORD` | the password you chose on export | — |

If Keychain Access only shows an *Apple Development* certificate, Xcode has
been signing distribution builds with a cloud-managed cert: create one at
developer.apple.com → Certificates → **+** → *Apple Distribution* (needs a
CSR from Keychain Access → Certificate Assistant → *Request a Certificate
From a Certificate Authority*), download it, double-click to add it to the
keychain, then export the .p12 as above. Each team can hold up to 3.

| `IOS_APPSTORE_PROFILE_BASE64` | an **App Store Connect** distribution provisioning profile for `com.benvuolo.yardscout`, base64 | developer.apple.com → *Certificates, Identifiers & Profiles* → **Profiles** → **+** → under *Distribution* pick **App Store Connect** → Continue → App ID `com.benvuolo.yardscout` → Continue → select the Apple Distribution certificate you exported above → Continue → name `YardScout App Store CI` → **Generate** → **Download** → `base64 -i ~/Downloads/YardScout_App_Store_CI.mobileprovision \| pbcopy`. Profiles expire after a year — regenerate and update the secret when the run says so. |

The archive is signed manually with that certificate + profile (CI keychains
have no Apple Development certificate, which automatic signing would want
for the archive step). The API key is used for the upload.

## First run, in this order

1. **Android, internal track** (`track=internal`). Play processes it in
   minutes; check *Testing → Internal testing* in the console. Then run
   again with `track=production` (or promote the internal release in the
   console).
2. **iOS, TestFlight only** (`submit=false`). Apple processes the build in
   10–40 min; it appears under TestFlight → iOS builds. Then run with
   `submit=true` — the workflow waits for processing (up to an hour) and
   submits. If it times out, the build is already uploaded: re-run with
   the same version/build and `submit=true`, or submit from App Store
   Connect.

## Numbers

- Android `versionCode` must always increase (blank = current + 1);
  `versionName` is free text.
- iOS `CURRENT_PROJECT_VERSION` (build number) must be unique per marketing
  version; blank = the workflow run number, which only ever goes up.
- Keep both marketing versions in step by hand (e.g. 1.10 on both stores).

## Update prompts and forcing an update (1.12.9+)

Apps from 1.12.9 on check `/v1/app-version` at launch and whenever they come
back to the foreground (`backend/src/app_version.js`):

- **"Update available" card** — automatic. iOS shows it once a newer version
  is live on the App Store (`app-store-version.yml` checks App Store Connect
  every 2 h and records it in `docs/app-version.json`; run it by hand to skip
  the wait); Android 48 h after a production upload (`release-android.yml`
  records it). Dismissible, once per version.
- **Required update** — manual. Edit `docs/app-version.json` on GitHub and set
  `min.ios` / `min.android` to the oldest version still allowed (e.g. `"1.13"`),
  optionally with a `message`. Apps below it show a full-screen "Update
  YardScout" within ~10 minutes. Set it back to `""` to lift it. Only raise
  `min` to a version that is already **live** in that store, or people will be
  sent to a store page with nothing to update to.

## What the workflows deliberately don't do

- Screenshots/metadata other than release notes (`appstore-assets/`,
  `play-assets/` are updated by hand in the consoles).
- Rollout percentages (Android goes to 100% of the chosen track).
- Any change to the keystore or certificates — losing the Android upload
  key means a Play support ticket, so the keystore stays only in the secret
  and in `~/yardscout-android/` on the Mac.
