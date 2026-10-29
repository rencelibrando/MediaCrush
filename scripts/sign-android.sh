#!/usr/bin/env bash
set -euo pipefail

# 1. Locate release APK
APK_IN=$(find build -name "*release-unsigned.apk" -o -name "*release.apk" 2>/dev/null | head -n 1)
if [ -z "$APK_IN" ] || [ ! -f "$APK_IN" ]; then
    APK_IN=$(find build -name "*.apk" 2>/dev/null | head -n 1)
fi

if [ -z "$APK_IN" ] || [ ! -f "$APK_IN" ]; then
    echo "Error: No APK found under build directory"
    exit 1
fi

mkdir -p release-artifacts
APK_OUT="release-artifacts/MediaCrush-Android.apk"

# 2. Locate Android build tools
BUILD_TOOLS_DIR=""
if [ -n "${ANDROID_HOME:-}" ] && [ -d "$ANDROID_HOME/build-tools" ]; then
    BUILD_TOOLS_DIR=$(find "$ANDROID_HOME/build-tools" -maxdepth 1 -mindepth 1 | sort -V | tail -n 1)
elif [ -n "${ANDROID_SDK_ROOT:-}" ] && [ -d "$ANDROID_SDK_ROOT/build-tools" ]; then
    BUILD_TOOLS_DIR=$(find "$ANDROID_SDK_ROOT/build-tools" -maxdepth 1 -mindepth 1 | sort -V | tail -n 1)
fi

# 3. Setup Keystore
KEYSTORE="release.keystore"
KS_PASS="android"
KEY_ALIAS="mediacrush"
KEY_PASS="android"

if [ -n "${ANDROID_KEYSTORE_BASE64:-}" ]; then
    echo "Using provided repository signing keystore"
    echo "$ANDROID_KEYSTORE_BASE64" | base64 -d > "$KEYSTORE"
    KS_PASS="${ANDROID_KEYSTORE_PASSWORD:-android}"
    KEY_ALIAS="${ANDROID_KEY_ALIAS:-mediacrush}"
    KEY_PASS="${ANDROID_KEY_PASSWORD:-android}"
elif [ ! -f "$KEYSTORE" ]; then
    echo "Generating release signing keystore"
    keytool -genkeypair -v \
        -keystore "$KEYSTORE" \
        -alias "$KEY_ALIAS" \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass "$KS_PASS" \
        -keypass "$KEY_PASS" \
        -dname "CN=MediaCrush Release, O=MediaCrush, C=US"
fi

# 4. Zipalign and sign APK
if [ -n "$BUILD_TOOLS_DIR" ] && [ -f "$BUILD_TOOLS_DIR/zipalign" ] && [ -f "$BUILD_TOOLS_DIR/apksigner" ]; then
    echo "Using Android Build Tools at $BUILD_TOOLS_DIR"
    TMP_ALIGNED="/tmp/mediacrush-aligned.apk"
    rm -f "$TMP_ALIGNED"
    "$BUILD_TOOLS_DIR/zipalign" -p -f 4 "$APK_IN" "$TMP_ALIGNED"
    cp "$TMP_ALIGNED" "$APK_OUT"
    
    echo "Signing APK with apksigner (v1 + v2 scheme)"
    "$BUILD_TOOLS_DIR/apksigner" sign \
        --ks "$KEYSTORE" \
        --ks-pass "pass:$KS_PASS" \
        --ks-key-alias "$KEY_ALIAS" \
        --key-pass "pass:$KEY_PASS" \
        --v1-signing-enabled true \
        --v2-signing-enabled true \
        "$APK_OUT"
    
    echo "Verifying APK signature"
    "$BUILD_TOOLS_DIR/apksigner" verify --verbose "$APK_OUT"
else
    echo "apksigner not found in current environment, copying APK directly"
    cp "$APK_IN" "$APK_OUT"
fi

# 5. Handle AAB bundle if present
AAB_IN=$(find build -name "*.aab" 2>/dev/null | head -n 1)
if [ -n "$AAB_IN" ] && [ -f "$AAB_IN" ]; then
    AAB_OUT="release-artifacts/MediaCrush-Android.aab"
    cp "$AAB_IN" "$AAB_OUT"
    if command -v jarsigner >/dev/null 2>&1; then
        echo "Signing AAB bundle"
        jarsigner -keystore "$KEYSTORE" \
            -storepass "$KS_PASS" \
            -keypass "$KEY_PASS" \
            "$AAB_OUT" "$KEY_ALIAS"
    fi
fi

echo "Android release artifacts generated:"
ls -lh release-artifacts/

