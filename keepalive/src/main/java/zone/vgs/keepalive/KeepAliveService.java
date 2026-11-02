package zone.vgs.keepalive;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.os.PowerManager;
import android.view.accessibility.AccessibilityEvent;

/**
 * Holds a lightweight PARTIAL_WAKE_LOCK ("SonyKeepAlive:Keep") while enabled in Accessibility Settings.
 * On Sony BRAVIA TVs, HealthKeepService checks PowerManagerService.getInstance().getWakeLockParams()
 * during standby (ACTION_SCREEN_OFF) after 26 hours of uptime; seeing this WakeLock entry prevents
 * powerManager.reboot("watchdog2").
 */
public final class KeepAliveService extends AccessibilityService {
    private PowerManager.WakeLock wakeLock;

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        acquireKeepAlive();
    }

    private void acquireKeepAlive() {
        if (wakeLock == null) {
            PowerManager pm = getSystemService(PowerManager.class);
            if (pm != null) {
                wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "SonyKeepAlive:Keep");
                wakeLock.setReferenceCounted(false);
            }
        }
        if (wakeLock != null && !wakeLock.isHeld()) {
            wakeLock.acquire();
        }
    }

    private void releaseKeepAlive() {
        if (wakeLock != null && wakeLock.isHeld()) {
            try {
                wakeLock.release();
            } catch (RuntimeException ignored) {
            }
        }
    }

    @Override
    public boolean onUnbind(Intent intent) {
        releaseKeepAlive();
        return super.onUnbind(intent);
    }

    @Override
    public void onDestroy() {
        releaseKeepAlive();
        super.onDestroy();
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
    }

    @Override
    public void onInterrupt() {
    }
}
