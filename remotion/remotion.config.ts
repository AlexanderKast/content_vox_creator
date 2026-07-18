import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// Chromium headless competes for CPU with everything else on the box.
// The semaphore on the Python side assumes this stays at 1.
Config.setConcurrency(1);
