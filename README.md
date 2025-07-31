# Automower Resume Bot 🛠️

A self-recovering watchdog script for **Husqvarna Automower® EPOS** mowers (like the 430X NERA) that frequently get stuck in a **"Trapped" (error code 21)** state — especially following the **July 2025 firmware update**.

## 💡 Why This Exists

After a [firmware update in July-2025](https://www.husqvarna.com/ie/support/husqvarna-self-service/what-s-new-in-the-latest-firmware-update-for-automower-320nera-430x-nera-and-450x-nera-ka-70186/), I started experiencing frequent "Trapped" errors, even when the mower wasn’t actually stuck. In our case, the mower operated on terrain with roughly **15% incline**, well within its **50% supported incline** (25% at the border), but still ended up in a non-functional state.

The frustration grew as the mower would:

- Get stuck several times per day
- Require **manual intervention** to confirm the error and resume
- Exhibit this behavior **both in wet and dry conditions**, though wet weather increases the frequency
- Eventually pause mowing entirely until someone physically opens the app and presses “resume”

This bot was created to **restore true autonomy** to the mower.

## 🔄 What It Does

- Monitors the mower status via the **Husqvarna Automower Connect API**
- Detects when the mower enters an error state (`ERROR`, `FATAL_ERROR`, or `ERROR_AT_POWER_UP`)
- Automatically confirms the error (if confirmable)
- Waits for the mower to transition to `PAUSED`
- Sends a **ResumeSchedule** command
- Verifies that the mower successfully returns to `IN_OPERATION` or `RESTRICTED`
- Includes retries, backoff logic, and logging to avoid flooding the API or freezing the mower

## 🧰 How It Works

The script authenticates using the official Husqvarna OAuth2 client credentials flow.  
It runs continuously on a server (currently deployed on [Fly.io](https://fly.io)) and polls mower status every few minutes.

All credentials are passed via environment variables, and the script supports **multiple mowers** if needed.

## 🛡️ Built-In Safeguards

- Respects API rate limits
- Only resumes when the mower is confirmed to be in a `PAUSED` state
- Retries resume if the mower doesn’t actually move after command
- Includes full logging for diagnostics

## ✅ Use Cases

- Automower 430X NERA (EPOS only, **no boundary wire**)
- Other EPOS models facing similar "Trapped" or false error behavior
- Mowers in remote locations where physical intervention is a hassle
- Users who want **true autonomy restored** to their “robotic” mower

## 📌 Important Notes

- Requires Husqvarna Developer account and API credentials
- Does **not** modify or spoof mower logic — it uses **official API calls only**
- Fly.io is used for hosting, but any always-on server or VPS would work

---

**This script is meant for people who just want their mower to do its job — without babysitting it.**  
Pull requests, feedback, and ideas are welcome.
