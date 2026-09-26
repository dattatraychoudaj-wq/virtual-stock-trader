# Demo Video Script

Target length: 2:30. Record the browser at 1080p and 30 fps with microphone narration. Keep the dashboard readable, close unrelated windows, and turn off notifications before recording.

## Before Recording

1. Start the Flask app and open <http://127.0.0.1:5000/>.
2. Restart the app before the recording if you want a clean account. The account is in memory and resets when the app process restarts.
3. Confirm the page shows the available cash and the stock selector. Choose a stock with a CSV price at the selected time.
4. Keep the recording to the app window. Do not show passwords, account settings, or personal notifications.

## Timed Walkthrough

### 0:00–0:15 | Introduction

**Show:** Trading dashboard and available-cash summary.

**Say:** “This is Virtual Stock Trader, a paper-trading demo built with Flask. It uses generated historical CSV prices and virtual cash only; it does not place real market orders.”

### 0:15–0:40 | Historical Quote

**Show:** Choose `TCS`, select September 1, 2026 at 9:30 AM, then click **Check price**.

**Say:** “I can choose a stock and a timestamp from the sample market data. The quote is the latest available CSV price at or before the selected time.”

### 0:40–1:05 | Buy Shares

**Show:** Set quantity to `2`, click **Buy**, then show the success message and the cash/portfolio summary refreshing.

**Say:** “I’m buying two virtual shares. The app checks the available balance, deducts the trade cost, and adds the position using a weighted average purchase price.”

### 1:05–1:30 | Portfolio and Unrealized P/L

**Show:** The portfolio row and the account summary values.

**Say:** “The portfolio shows quantity, average purchase price, the latest price in the CSV, position value, and unrealized profit or loss. This valuation uses the latest sample-data price, not a live exchange feed.”

### 1:30–1:55 | Sell Shares

**Show:** Change the selected time to 12:00 PM on September 1, set quantity to `1`, and click **Sell**.

**Say:** “I’m selling one share at the selected historical time. The app rejects sales beyond the shares owned, credits the virtual proceeds, and reports realized profit or loss. The result may be a gain or a loss.”

### 1:55–2:15 | Transaction History

**Show:** Scroll to Transaction History and point out the buy and sell rows.

**Say:** “Each successful trade is recorded with its action, quantity, execution price, and selected trade time. The newest transactions appear first.”

### 2:15–2:30 | Technology and Close

**Show:** Return to the account summary or show the repository README.

**Say:** “The project uses Python and Flask for the API, SQLite for the in-memory account, and CSV for sample historical prices. The source and setup instructions are in the GitHub repository.”

## Recording and Publishing

- OBS Studio: capture the browser window, set output to 1920×1080 at 30 fps, select the microphone, and record to MP4. Make a short test recording first to check audio levels.
- Windows Game Bar: focus the browser, press `Win+Alt+R` to start or stop recording, and use `Win+G` to check capture and microphone settings.
- Speak clearly, keep the cursor near the control being discussed, and pause briefly after each action so the UI update is visible.
- Watch the complete export once before publishing. Check that the video and microphone audio are clear and that no unrelated private information appears.
- Upload the final video to an unlisted video host or attach it to a GitHub release, then replace the video-link placeholder in `README.md` with the share URL.
