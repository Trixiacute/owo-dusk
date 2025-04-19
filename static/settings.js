/*
This file is part of owo-dusk.

Copyright (c) 2024-present EchoQuill

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
*/

// Current settings data
let currentSettings = {};

// DOM Elements
const settingsNavItems = document.querySelectorAll('.settings-nav-item');
const settingsPanels = document.querySelectorAll('.settings-panel');
const configButtons = document.querySelectorAll('.setting-btn');
const modal = document.getElementById('configModal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const modalClose = document.querySelector('.modal-close');
const modalCancel = document.getElementById('modalCancel');
const modalSave = document.getElementById('modalSave');
const toast = document.getElementById('saveToast');
const exportBtn = document.getElementById('exportSettings');
const importBtn = document.getElementById('importSettings');
const resetBtn = document.getElementById('resetSettings');
const refreshIntervalSlider = document.getElementById('refreshInterval');
const refreshIntervalValue = refreshIntervalSlider.nextElementSibling;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
  // Load settings from server
  loadSettings();
  
  // Set up event listeners
  setupEventListeners();
});

// Load settings from server
async function loadSettings() {
  try {
    const response = await fetch('/api/config', {
      headers: {
        'password': 'password'
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to load settings');
    }
    
    currentSettings = await response.json();
    
    // Populate form with loaded settings
    populateSettings();
  } catch (error) {
    console.error('Error loading settings:', error);
    showToast('Failed to load settings. Please try again.');
  }
}

// Populate form fields with current settings
function populateSettings() {
  // General Settings
  document.getElementById('offlineStatus').checked = currentSettings.offlineStatus;
  document.getElementById('typingIndicator').checked = currentSettings.typingIndicator;
  document.getElementById('silentMessages').checked = currentSettings.silentTextMessages;
  document.getElementById('prefix').value = currentSettings.setprefix;
  document.getElementById('useSlashCommands').checked = currentSettings.useSlashCommands;
  document.getElementById('websiteEnabled').checked = currentSettings.website.enabled;
  document.getElementById('websitePort').value = currentSettings.website.port;
  document.getElementById('refreshInterval').value = currentSettings.website.refreshInterval;
  refreshIntervalValue.textContent = `${currentSettings.website.refreshInterval}s`;
  
  // Channel Switcher Settings
  document.getElementById('channelSwitcherEnabled').checked = currentSettings.channel_switcher?.enabled || false;
  
  // Commands Settings
  document.getElementById('huntEnabled').checked = currentSettings.commands.hunt.enabled;
  document.getElementById('battleEnabled').checked = currentSettings.commands.battle.enabled;
  document.getElementById('owoEnabled').checked = currentSettings.commands.owo.enabled;
  document.getElementById('levelEnabled').checked = currentSettings.commands.lvlGrind.enabled;
  document.getElementById('prayEnabled').checked = currentSettings.commands.pray.enabled;
  document.getElementById('cookieEnabled').checked = currentSettings.commands.cookie.enabled;
  document.getElementById('sellEnabled').checked = currentSettings.commands.sell.enabled;
  document.getElementById('huntbotEnabled').checked = currentSettings.commands.autoHuntBot.enabled;
  document.getElementById('dailyEnabled').checked = currentSettings.autoDaily;
  document.getElementById('lotteryEnabled').checked = currentSettings.commands.lottery.enabled;
  document.getElementById('lootboxEnabled').checked = currentSettings.autoUse.autoLootbox;
  document.getElementById('crateEnabled').checked = currentSettings.autoUse.autoCrate;
  document.getElementById('gemsEnabled').checked = currentSettings.autoUse.gems.enabled;
  
  // Captcha Settings
  document.getElementById('misspellEnabled').checked = currentSettings.misspell.enabled;
  document.getElementById('sleepEnabled').checked = currentSettings.sleep.enabled;
  document.getElementById('webhookEnabled').checked = currentSettings.webhook.enabled;
  document.getElementById('desktopNotifEnabled').checked = currentSettings.captcha.toastOrPopup.enabled;
  document.getElementById('audioEnabled').checked = currentSettings.captcha.playAudio.enabled;
  document.getElementById('mobileEnabled').checked = currentSettings.captcha.termux.vibrate.enabled;
  
  // Gambling Settings
  document.getElementById('gambleAmount').value = currentSettings.gamble.allottedAmount;
  document.getElementById('goalEnabled').checked = currentSettings.gamble.goalSystem.enabled;
  document.getElementById('goalAmount').value = currentSettings.gamble.goalSystem.amount;
  document.getElementById('coinflipEnabled').checked = currentSettings.gamble.coinflip.enabled;
  document.getElementById('slotsEnabled').checked = currentSettings.gamble.slots.enabled;
  
  // Notification Settings
  document.getElementById('webhookUrl').value = currentSettings.webhook.webhookUrl || '';
  document.getElementById('webhookCaptchaUrl').value = currentSettings.webhook.webhookCaptchaUrl || '';
  document.getElementById('webhookPingId').value = currentSettings.webhook.webhookUserIdToPingOnCaptcha || '';
  document.getElementById('webhookUselessLog').checked = currentSettings.webhook.webhookUselessLog;
  document.getElementById('captchaContent').value = currentSettings.captcha.notifications.captchaContent;
  document.getElementById('bannedContent').value = currentSettings.captcha.notifications.bannedContent;
  
  // Advanced Settings
  document.getElementById('debugEnabled').checked = currentSettings.debug.enabled;
  document.getElementById('logFileEnabled').checked = currentSettings.debug.logInTextFile;
  document.getElementById('batteryCheckEnabled').checked = currentSettings.batteryCheck.enabled;
  document.getElementById('minBattery').value = currentSettings.batteryCheck.minPercentage;
  document.getElementById('batteryInterval').value = currentSettings.batteryCheck.refreshInterval;
}

// Set up all event listeners
function setupEventListeners() {
  // Navigation between tabs
  settingsNavItems.forEach(item => {
    item.addEventListener('click', () => {
      const target = item.getAttribute('data-target');
      
      // Update active nav item
      settingsNavItems.forEach(navItem => navItem.classList.remove('active'));
      item.classList.add('active');
      
      // Show the corresponding panel
      settingsPanels.forEach(panel => {
        panel.classList.remove('active');
        if (panel.id === target) {
          panel.classList.add('active');
        }
      });
    });
  });
  
  // Config buttons to open modal
  configButtons.forEach(button => {
    button.addEventListener('click', () => {
      const settingType = button.getAttribute('data-settings');
      openConfigModal(settingType);
    });
  });
  
  // Modal close buttons
  modalClose.addEventListener('click', closeModal);
  modalCancel.addEventListener('click', closeModal);
  
  // Modal save button
  modalSave.addEventListener('click', saveModalSettings);
  
  // Refresh interval slider
  refreshIntervalSlider.addEventListener('input', () => {
    refreshIntervalValue.textContent = `${refreshIntervalSlider.value}s`;
  });
  
  // Export settings
  exportBtn.addEventListener('click', exportSettings);
  
  // Import settings
  importBtn.addEventListener('click', () => {
    // Create a file input element
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.json';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);
    
    fileInput.addEventListener('change', importSettingsFile);
    fileInput.click();
    
    // Remove the element after selection
    setTimeout(() => {
      document.body.removeChild(fileInput);
    }, 1000);
  });
  
  // Reset settings
  resetBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to reset all settings to default values? This cannot be undone.')) {
      resetSettings();
    }
  });
  
  // Save all settings button
  document.querySelectorAll('input').forEach(input => {
    input.addEventListener('change', () => {
      updateSettingsFromForm();
    });
  });
}

// Open configuration modal for specific setting type
function openConfigModal(settingType) {
  let title = '';
  let content = '';
  
  switch (settingType) {
    case 'hunt':
      title = 'Hunt Command Settings';
      content = createHuntSettingsForm();
      break;
    case 'battle':
      title = 'Battle Command Settings';
      content = createBattleSettingsForm();
      break;
    case 'owo':
      title = 'OwO Command Settings';
      content = createOwoSettingsForm();
      break;
    case 'level':
      title = 'Level Grinding Settings';
      content = createLevelSettingsForm();
      break;
    case 'pray':
      title = 'Pray/Curse Settings';
      content = createPraySettingsForm();
      break;
    case 'cookie':
      title = 'Cookie Settings';
      content = createCookieSettingsForm();
      break;
    case 'sell':
      title = 'Sell/Sacrifice Settings';
      content = createSellSettingsForm();
      break;
    case 'huntbot':
      title = 'HuntBot Settings';
      content = createHuntbotSettingsForm();
      break;
    case 'gems':
      title = 'Gems Settings';
      content = createGemsSettingsForm();
      break;
    case 'misspell':
      title = 'Misspelling Settings';
      content = createMisspellSettingsForm();
      break;
    case 'sleep':
      title = 'Random Sleep Settings';
      content = createSleepSettingsForm();
      break;
    case 'webhook':
      title = 'Webhook Settings';
      content = createWebhookSettingsForm();
      break;
    case 'desktop':
      title = 'Desktop Notification Settings';
      content = createDesktopNotifSettingsForm();
      break;
    case 'audio':
      title = 'Audio Notification Settings';
      content = createAudioSettingsForm();
      break;
    case 'mobile':
      title = 'Mobile Notification Settings';
      content = createMobileSettingsForm();
      break;
    case 'coinflip':
      title = 'Coinflip Settings';
      content = createCoinflipSettingsForm();
      break;
    case 'slots':
      title = 'Slots Settings';
      content = createSlotsSettingsForm();
      break;
    case 'channelSwitcher':
      title = 'Channel Switcher Settings';
      content = createChannelSwitcherSettingsForm();
      break;
    case 'websiteSecurity':
      title = 'Website Security Settings';
      content = createWebsiteSecuritySettingsForm();
      break;
    case 'websiteFeatures':
      title = 'Website Features Settings';
      content = createWebsiteFeaturesSettingsForm();
      break;
    case 'websiteAppearance':
      title = 'Website Appearance Settings';
      content = createWebsiteAppearanceSettingsForm();
      break;
    default:
      title = 'Configure Settings';
      content = '<p>Settings not available.</p>';
  }
  
  modalTitle.textContent = title;
  modalBody.innerHTML = content;
  modal.style.display = 'block';
  
  // Store current setting type for saving
  modalSave.setAttribute('data-setting-type', settingType);
}

// Close the modal
function closeModal() {
  modal.style.display = 'none';
}

// Save settings from modal
function saveModalSettings() {
  const settingType = modalSave.getAttribute('data-setting-type');
  
  switch (settingType) {
    case 'hunt':
      saveHuntSettings();
      break;
    case 'battle':
      saveBattleSettings();
      break;
    case 'owo':
      saveOwoSettings();
      break;
    case 'level':
      saveLevelSettings();
      break;
    case 'pray':
      savePraySettings();
      break;
    case 'cookie':
      saveCookieSettings();
      break;
    case 'sell':
      saveSellSettings();
      break;
    case 'huntbot':
      saveHuntbotSettings();
      break;
    case 'gems':
      saveGemsSettings();
      break;
    case 'misspell':
      saveMisspellSettings();
      break;
    case 'sleep':
      saveSleepSettings();
      break;
    case 'webhook':
      saveWebhookSettings();
      break;
    case 'desktop':
      saveDesktopNotifSettings();
      break;
    case 'audio':
      saveAudioSettings();
      break;
    case 'mobile':
      saveMobileSettings();
      break;
    case 'coinflip':
      saveCoinflipSettings();
      break;
    case 'slots':
      saveSlotsSettings();
      break;
    case 'channelSwitcher':
      saveChannelSwitcherSettings();
      break;
    case 'websiteSecurity':
      saveWebsiteSecuritySettings();
      break;
    case 'websiteFeatures':
      saveWebsiteFeaturesSettings();
      break;
    case 'websiteAppearance':
      saveWebsiteAppearanceSettings();
      break;
  }
  
  // Save settings to server
  saveSettings();
  
  // Close the modal
  closeModal();
}

// Update settings object from form values
function updateSettingsFromForm() {
  // General Settings
  currentSettings.offlineStatus = document.getElementById('offlineStatus').checked;
  currentSettings.typingIndicator = document.getElementById('typingIndicator').checked;
  currentSettings.silentTextMessages = document.getElementById('silentMessages').checked;
  currentSettings.setprefix = document.getElementById('prefix').value;
  currentSettings.useSlashCommands = document.getElementById('useSlashCommands').checked;
  currentSettings.website.enabled = document.getElementById('websiteEnabled').checked;
  currentSettings.website.port = parseInt(document.getElementById('websitePort').value);
  currentSettings.website.refreshInterval = parseInt(document.getElementById('refreshInterval').value);
  
  // Initialize website security, features, and appearance if they don't exist
  if (!currentSettings.website.security) {
    currentSettings.website.security = {
      enabled: false,
      login_required: false,
      username: "admin",
      password: "changeme",
      allow_config_edit: true,
      ip_whitelist: [],
      session_timeout: 3600
    };
  }
  
  if (!currentSettings.website.features) {
    currentSettings.website.features = {
      dashboard: true,
      settings: true,
      stats: true,
      logs: true,
      commands: true,
      restart: true
    };
  }
  
  if (!currentSettings.website.appearance) {
    currentSettings.website.appearance = {
      theme: "dark",
      accent_color: "#70af87",
      show_username: true,
      show_avatar: true,
      custom_title: "OwO Dusk Dashboard"
    };
  }
  
  // Channel Switcher Settings
  if (!currentSettings.channel_switcher) {
    currentSettings.channel_switcher = {};
  }
  currentSettings.channel_switcher.enabled = document.getElementById('channelSwitcherEnabled').checked;
  
  // Commands Settings
  currentSettings.commands.hunt.enabled = document.getElementById('huntEnabled').checked;
  currentSettings.commands.battle.enabled = document.getElementById('battleEnabled').checked;
  currentSettings.commands.owo.enabled = document.getElementById('owoEnabled').checked;
  currentSettings.commands.lvlGrind.enabled = document.getElementById('levelEnabled').checked;
  currentSettings.commands.pray.enabled = document.getElementById('prayEnabled').checked;
  currentSettings.commands.cookie.enabled = document.getElementById('cookieEnabled').checked;
  currentSettings.commands.sell.enabled = document.getElementById('sellEnabled').checked;
  currentSettings.commands.autoHuntBot.enabled = document.getElementById('huntbotEnabled').checked;
  currentSettings.autoDaily = document.getElementById('dailyEnabled').checked;
  currentSettings.commands.lottery.enabled = document.getElementById('lotteryEnabled').checked;
  currentSettings.autoUse.autoLootbox = document.getElementById('lootboxEnabled').checked;
  currentSettings.autoUse.autoCrate = document.getElementById('crateEnabled').checked;
  currentSettings.autoUse.gems.enabled = document.getElementById('gemsEnabled').checked;
  
  // Captcha Settings
  currentSettings.misspell.enabled = document.getElementById('misspellEnabled').checked;
  currentSettings.sleep.enabled = document.getElementById('sleepEnabled').checked;
  currentSettings.webhook.enabled = document.getElementById('webhookEnabled').checked;
  currentSettings.captcha.toastOrPopup.enabled = document.getElementById('desktopNotifEnabled').checked;
  currentSettings.captcha.playAudio.enabled = document.getElementById('audioEnabled').checked;
  currentSettings.captcha.termux.vibrate.enabled = document.getElementById('mobileEnabled').checked;
  
  // Gambling Settings
  currentSettings.gamble.allottedAmount = parseInt(document.getElementById('gambleAmount').value);
  currentSettings.gamble.goalSystem.enabled = document.getElementById('goalEnabled').checked;
  currentSettings.gamble.goalSystem.amount = parseInt(document.getElementById('goalAmount').value);
  currentSettings.gamble.coinflip.enabled = document.getElementById('coinflipEnabled').checked;
  currentSettings.gamble.slots.enabled = document.getElementById('slotsEnabled').checked;
  
  // Notification Settings
  currentSettings.webhook.webhookUrl = document.getElementById('webhookUrl').value;
  currentSettings.webhook.webhookCaptchaUrl = document.getElementById('webhookCaptchaUrl').value;
  currentSettings.webhook.webhookUserIdToPingOnCaptcha = document.getElementById('webhookPingId').value;
  currentSettings.webhook.webhookUselessLog = document.getElementById('webhookUselessLog').checked;
  currentSettings.captcha.notifications.captchaContent = document.getElementById('captchaContent').value;
  currentSettings.captcha.notifications.bannedContent = document.getElementById('bannedContent').value;
  
  // Advanced Settings
  currentSettings.debug.enabled = document.getElementById('debugEnabled').checked;
  currentSettings.debug.logInTextFile = document.getElementById('logFileEnabled').checked;
  currentSettings.batteryCheck.enabled = document.getElementById('batteryCheckEnabled').checked;
  currentSettings.batteryCheck.minPercentage = parseInt(document.getElementById('minBattery').value);
  currentSettings.batteryCheck.refreshInterval = parseInt(document.getElementById('batteryInterval').value);
  
  // Auto-save changes
  saveSettings();
}

// Save settings to server
async function saveSettings() {
  try {
    const response = await fetch('/api/saveThings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(currentSettings)
    });
    
    if (!response.ok) {
      throw new Error('Failed to save settings');
    }
    
    showToast('Settings saved successfully!');
  } catch (error) {
    console.error('Error saving settings:', error);
    showToast('Failed to save settings. Please try again.');
  }
}

// Export settings to a file
function exportSettings() {
  const dataStr = JSON.stringify(currentSettings, null, 2);
  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
  
  const exportFileDefaultName = `owo-dusk-settings-${new Date().toISOString().slice(0,10)}.json`;
  
  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', dataUri);
  linkElement.setAttribute('download', exportFileDefaultName);
  linkElement.click();
  
  showToast('Settings exported successfully!');
}

// Import settings from a file
function importSettingsFile(event) {
  const file = event.target.files[0];
  
  if (!file) {
    return;
  }
  
  const reader = new FileReader();
  
  reader.onload = function(e) {
    try {
      const importedSettings = JSON.parse(e.target.result);
      
      // Apply the imported settings
      currentSettings = importedSettings;
      
      // Update form values
      populateSettings();
      
      // Save to server
      saveSettings();
      
      showToast('Settings imported successfully!');
    } catch (error) {
      console.error('Error parsing settings file:', error);
      showToast('Failed to import settings. Invalid file format.');
    }
  };
  
  reader.readAsText(file);
}

// Reset settings to defaults
function resetSettings() {
  // Reload the page - the server will use default settings
  window.location.reload();
}

// Show toast notification
function showToast(message) {
  toast.textContent = message;
  toast.className = 'toast show';
  
  // Hide after 3 seconds
  setTimeout(() => {
    toast.className = 'toast';
  }, 3000);
}

// Create form for Hunt settings
function createHuntSettingsForm() {
  return `
    <div class="modal-form-group">
      <label class="modal-label">Cooldown (seconds)</label>
      <div style="display: flex; gap: 10px;">
        <input type="number" class="modal-input" id="huntCooldownMin" value="${currentSettings.commands.hunt.cooldown[0]}" placeholder="Min">
        <input type="number" class="modal-input" id="huntCooldownMax" value="${currentSettings.commands.hunt.cooldown[1]}" placeholder="Max">
      </div>
    </div>
    <div class="modal-form-group">
      <label class="modal-label">Use Short Form</label>
      <label class="toggle">
        <input type="checkbox" id="huntShortForm" ${currentSettings.commands.hunt.useShortForm ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <span style="color: #aaa; font-size: 12px; margin-left: 10px;">Use "h" instead of "hunt"</span>
    </div>
  `;
}

// Save Hunt settings
function saveHuntSettings() {
  currentSettings.commands.hunt.cooldown = [
    parseFloat(document.getElementById('huntCooldownMin').value),
    parseFloat(document.getElementById('huntCooldownMax').value)
  ];
  currentSettings.commands.hunt.useShortForm = document.getElementById('huntShortForm').checked;
}

// Create form for Battle settings
function createBattleSettingsForm() {
  return `
    <div class="modal-form-group">
      <label class="modal-label">Cooldown (seconds)</label>
      <div style="display: flex; gap: 10px;">
        <input type="number" class="modal-input" id="battleCooldownMin" value="${currentSettings.commands.battle.cooldown[0]}" placeholder="Min">
        <input type="number" class="modal-input" id="battleCooldownMax" value="${currentSettings.commands.battle.cooldown[1]}" placeholder="Max">
      </div>
    </div>
    <div class="modal-form-group">
      <label class="modal-label">Use Short Form</label>
      <label class="toggle">
        <input type="checkbox" id="battleShortForm" ${currentSettings.commands.battle.useShortForm ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <span style="color: #aaa; font-size: 12px; margin-left: 10px;">Use "b" instead of "battle"</span>
    </div>
  `;
}

// Save Battle settings
function saveBattleSettings() {
  currentSettings.commands.battle.cooldown = [
    parseFloat(document.getElementById('battleCooldownMin').value),
    parseFloat(document.getElementById('battleCooldownMax').value)
  ];
  currentSettings.commands.battle.useShortForm = document.getElementById('battleShortForm').checked;
}

// Create form for OwO settings
function createOwoSettingsForm() {
  return `
    <div class="modal-form-group">
      <label class="modal-label">Cooldown (seconds)</label>
      <div style="display: flex; gap: 10px;">
        <input type="number" class="modal-input" id="owoCooldownMin" value="${currentSettings.commands.owo.cooldown[0]}" placeholder="Min">
        <input type="number" class="modal-input" id="owoCooldownMax" value="${currentSettings.commands.owo.cooldown[1]}" placeholder="Max">
      </div>
    </div>
  `;
}

// Save OwO settings
function saveOwoSettings() {
  currentSettings.commands.owo.cooldown = [
    parseFloat(document.getElementById('owoCooldownMin').value),
    parseFloat(document.getElementById('owoCooldownMax').value)
  ];
}

// Sample implementation for the rest of the modal forms
// For brevity, I'm not including all of them in full detail

function createLevelSettingsForm() {
  return `
    <div class="modal-form-group">
      <label class="modal-label">Cooldown (seconds)</label>
      <div style="display: flex; gap: 10px;">
        <input type="number" class="modal-input" id="levelCooldownMin" value="${currentSettings.commands.lvlGrind.cooldown[0]}" placeholder="Min">
        <input type="number" class="modal-input" id="levelCooldownMax" value="${currentSettings.commands.lvlGrind.cooldown[1]}" placeholder="Max">
      </div>
    </div>
    <div class="modal-form-group">
      <label class="modal-label">Use Quote Instead</label>
      <label class="toggle">
        <input type="checkbox" id="levelUseQuote" ${currentSettings.commands.lvlGrind.useQuoteInstead ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
    </div>
    <div class="modal-form-group">
      <label class="modal-label">Random String Length</label>
      <div style="display: flex; gap: 10px;">
        <input type="number" class="modal-input" id="levelMinLength" value="${currentSettings.commands.lvlGrind.minLengthForRandomString}" placeholder="Min">
        <input type="number" class="modal-input" id="levelMaxLength" value="${currentSettings.commands.lvlGrind.maxLengthForRandomString}" placeholder="Max">
      </div>
    </div>
  `;
}

function saveLevelSettings() {
  currentSettings.commands.lvlGrind.cooldown = [
    parseFloat(document.getElementById('levelCooldownMin').value),
    parseFloat(document.getElementById('levelCooldownMax').value)
  ];
  currentSettings.commands.lvlGrind.useQuoteInstead = document.getElementById('levelUseQuote').checked;
  currentSettings.commands.lvlGrind.minLengthForRandomString = parseInt(document.getElementById('levelMinLength').value);
  currentSettings.commands.lvlGrind.maxLengthForRandomString = parseInt(document.getElementById('levelMaxLength').value);
}

// Placeholder implementations for other modal forms
function createPraySettingsForm() { return '<p>Form not yet implemented</p>'; }
function savePraySettings() {}

function createCookieSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveCookieSettings() {}

function createSellSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveSellSettings() {}

function createHuntbotSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveHuntbotSettings() {}

function createGemsSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveGemsSettings() {}

function createMisspellSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveMisspellSettings() {}

function createSleepSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveSleepSettings() {}

function createWebhookSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveWebhookSettings() {}

function createDesktopNotifSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveDesktopNotifSettings() {}

function createAudioSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveAudioSettings() {}

function createMobileSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveMobileSettings() {}

function createCoinflipSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveCoinflipSettings() {}

function createSlotsSettingsForm() { return '<p>Form not yet implemented</p>'; }
function saveSlotsSettings() {}

function createChannelSwitcherSettingsForm() {
  const settings = currentSettings.channel_switcher || {};
  const switchInterval = settings.switch_interval || [5, 15];
  const commandsPerSwitch = settings.commands_per_switch || [3, 8];
  const channels = settings.channels || [];
  const threads = settings.threads || { enabled: false, parent_channel: 0, thread_ids: [] };
  
  return `
    <div class="settings-form">
      <div class="form-group">
        <label>Switch Interval (minutes)</label>
        <div class="range-input-group">
          <input type="number" id="switchIntervalMin" value="${switchInterval[0]}" min="1" max="60">
          <span>to</span>
          <input type="number" id="switchIntervalMax" value="${switchInterval[1]}" min="1" max="120">
        </div>
        <div class="help-text">Random time interval between channel switches</div>
      </div>
      
      <div class="form-group">
        <label>Commands Per Switch</label>
        <div class="range-input-group">
          <input type="number" id="commandsPerSwitchMin" value="${commandsPerSwitch[0]}" min="1" max="50">
          <span>to</span>
          <input type="number" id="commandsPerSwitchMax" value="${commandsPerSwitch[1]}" min="1" max="100">
        </div>
        <div class="help-text">Random command count before switching channels</div>
      </div>
      
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="smartSwitching" ${settings.smart_switching ? 'checked' : ''}>
          Smart Switching
        </label>
        <div class="help-text">Intelligently decide when to switch channels</div>
      </div>
      
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="switchOnSlowmode" ${settings.switch_on_slowmode ? 'checked' : ''}>
          Switch on Slowmode
        </label>
        <div class="help-text">Switch channels when slowmode is detected</div>
      </div>
      
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="avoidActiveChannels" ${settings.avoid_active_channels ? 'checked' : ''}>
          Avoid Active Channels
        </label>
        <div class="help-text">Switch from channels with high user activity</div>
      </div>
      
      <div class="form-group">
        <label>Channel IDs (comma separated)</label>
        <textarea id="channelIds" rows="3" placeholder="Enter channel IDs separated by commas">${channels.join(', ')}</textarea>
        <div class="help-text">List of channel IDs to switch between</div>
      </div>
      
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="threadsEnabled" ${threads.enabled ? 'checked' : ''}>
          Enable Thread Switching
        </label>
        <div class="help-text">Include threads in channel switching</div>
      </div>
      
      <div class="form-group">
        <label>Parent Channel ID</label>
        <input type="number" id="parentChannelId" value="${threads.parent_channel || 0}">
        <div class="help-text">ID of the channel containing threads</div>
      </div>
      
      <div class="form-group">
        <label>Thread IDs (comma separated)</label>
        <textarea id="threadIds" rows="3" placeholder="Enter thread IDs separated by commas">${threads.thread_ids?.join(', ') || ''}</textarea>
        <div class="help-text">List of thread IDs to switch between</div>
      </div>
    </div>
  `;
}

function saveChannelSwitcherSettings() {
  const channels = document.getElementById('channelIds').value.split(',')
    .map(id => id.trim())
    .filter(id => id && !isNaN(id))
    .map(id => parseInt(id));
    
  const threadIds = document.getElementById('threadIds').value.split(',')
    .map(id => id.trim())
    .filter(id => id && !isNaN(id))
    .map(id => parseInt(id));
    
  currentSettings.channel_switcher = {
    enabled: currentSettings.channel_switcher?.enabled || false,
    channels: channels,
    threads: {
      enabled: document.getElementById('threadsEnabled').checked,
      parent_channel: parseInt(document.getElementById('parentChannelId').value) || 0,
      thread_ids: threadIds
    },
    switch_interval: [
      parseInt(document.getElementById('switchIntervalMin').value) || 5,
      parseInt(document.getElementById('switchIntervalMax').value) || 15
    ],
    commands_per_switch: [
      parseInt(document.getElementById('commandsPerSwitchMin').value) || 3,
      parseInt(document.getElementById('commandsPerSwitchMax').value) || 8
    ],
    smart_switching: document.getElementById('smartSwitching').checked,
    switch_on_slowmode: document.getElementById('switchOnSlowmode').checked,
    avoid_active_channels: document.getElementById('avoidActiveChannels').checked
  };
}

// Create form for Website Security settings
function createWebsiteSecuritySettingsForm() {
  const security = currentSettings.website.security;
  
  return `
    <div class="modal-form-group">
      <label class="modal-label">Enable Security Features</label>
      <label class="toggle">
        <input type="checkbox" id="securityEnabled" ${security.enabled ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Enable security features for the dashboard</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Require Login</label>
      <label class="toggle">
        <input type="checkbox" id="loginRequired" ${security.login_required ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Require username and password to access dashboard</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Username</label>
      <input type="text" class="modal-input" id="securityUsername" value="${security.username}">
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Password</label>
      <input type="password" class="modal-input" id="securityPassword" value="${security.password}">
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Allow Config Editing</label>
      <label class="toggle">
        <input type="checkbox" id="allowConfigEdit" ${security.allow_config_edit ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Allow editing configuration from dashboard</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">IP Whitelist (comma separated)</label>
      <input type="text" class="modal-input" id="ipWhitelist" value="${security.ip_whitelist.join(', ')}">
      <div class="setting-description">Only these IPs can access the dashboard (empty = all allowed)</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Session Timeout (seconds)</label>
      <input type="number" class="modal-input" id="sessionTimeout" value="${security.session_timeout}">
      <div class="setting-description">Time until login expires</div>
    </div>
  `;
}

// Save Website Security settings
function saveWebsiteSecuritySettings() {
  const security = currentSettings.website.security;
  
  security.enabled = document.getElementById('securityEnabled').checked;
  security.login_required = document.getElementById('loginRequired').checked;
  security.username = document.getElementById('securityUsername').value;
  security.password = document.getElementById('securityPassword').value;
  security.allow_config_edit = document.getElementById('allowConfigEdit').checked;
  
  // Process IP whitelist
  const ipList = document.getElementById('ipWhitelist').value
    .split(',')
    .map(ip => ip.trim())
    .filter(ip => ip);
    
  security.ip_whitelist = ipList;
  security.session_timeout = parseInt(document.getElementById('sessionTimeout').value);
}

// Create form for Website Features settings
function createWebsiteFeaturesSettingsForm() {
  const features = currentSettings.website.features;
  
  return `
    <div class="modal-form-group">
      <label class="modal-label">Dashboard Page</label>
      <label class="toggle">
        <input type="checkbox" id="featureDashboard" ${features.dashboard ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Enable main dashboard page</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Settings Page</label>
      <label class="toggle">
        <input type="checkbox" id="featureSettings" ${features.settings ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Enable settings configuration page</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Statistics</label>
      <label class="toggle">
        <input type="checkbox" id="featureStats" ${features.stats ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Show statistics on dashboard</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Logs</label>
      <label class="toggle">
        <input type="checkbox" id="featureLogs" ${features.logs ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Show log console on dashboard</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Command Controls</label>
      <label class="toggle">
        <input type="checkbox" id="featureCommands" ${features.commands ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Show command controls on dashboard</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Restart Button</label>
      <label class="toggle">
        <input type="checkbox" id="featureRestart" ${features.restart ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Show restart button on dashboard</div>
    </div>
  `;
}

// Save Website Features settings
function saveWebsiteFeaturesSettings() {
  const features = currentSettings.website.features;
  
  features.dashboard = document.getElementById('featureDashboard').checked;
  features.settings = document.getElementById('featureSettings').checked;
  features.stats = document.getElementById('featureStats').checked;
  features.logs = document.getElementById('featureLogs').checked;
  features.commands = document.getElementById('featureCommands').checked;
  features.restart = document.getElementById('featureRestart').checked;
}

// Create form for Website Appearance settings
function createWebsiteAppearanceSettingsForm() {
  const appearance = currentSettings.website.appearance;
  
  return `
    <div class="modal-form-group">
      <label class="modal-label">Theme</label>
      <select class="modal-input" id="themeSelect">
        <option value="dark" ${appearance.theme === 'dark' ? 'selected' : ''}>Dark</option>
        <option value="light" ${appearance.theme === 'light' ? 'selected' : ''}>Light</option>
        <option value="purple" ${appearance.theme === 'purple' ? 'selected' : ''}>Purple</option>
        <option value="custom" ${appearance.theme === 'custom' ? 'selected' : ''}>Custom</option>
      </select>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Accent Color</label>
      <input type="color" class="modal-color-input" id="accentColor" value="${appearance.accent_color}">
      <div class="setting-description">Main highlight color</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Show Username</label>
      <label class="toggle">
        <input type="checkbox" id="showUsername" ${appearance.show_username ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Display bot username in header</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Show Avatar</label>
      <label class="toggle">
        <input type="checkbox" id="showAvatar" ${appearance.show_avatar ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="setting-description">Display bot avatar in header</div>
    </div>

    <div class="modal-form-group">
      <label class="modal-label">Custom Title</label>
      <input type="text" class="modal-input" id="customTitle" value="${appearance.custom_title}">
      <div class="setting-description">Custom page title for dashboard</div>
    </div>
  `;
}

// Save Website Appearance settings
function saveWebsiteAppearanceSettings() {
  const appearance = currentSettings.website.appearance;
  
  appearance.theme = document.getElementById('themeSelect').value;
  appearance.accent_color = document.getElementById('accentColor').value;
  appearance.show_username = document.getElementById('showUsername').checked;
  appearance.show_avatar = document.getElementById('showAvatar').checked;
  appearance.custom_title = document.getElementById('customTitle').value;
} 