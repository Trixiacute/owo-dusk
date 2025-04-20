/*
This file is part of owo-dusk.

Copyright (c) 2024-present EchoQuill

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
*/

// Advanced Stats for the OwO Dusk Dashboard
let statsData = {};
let statsHistory = {
  currency: [],
  commands: {},
  timestamps: [],
  earnings: {
    hourly: [],
    daily: [],
    weekly: []
  },
  resources: {
    cpu: [],
    memory: [],
    latency: []
  }
};

// Settings for charts
const chartSettings = {
  refreshInterval: 10000, // 10 seconds refresh interval
  historyLength: 100, // Data points to keep in history
  chartColors: {
    currency: {
      primary: '#FF79C3',
      background: 'rgba(255, 121, 195, 0.1)'
    },
    commands: {
      hunt: { primary: '#4CAF50', background: 'rgba(76, 175, 80, 0.8)' },
      battle: { primary: '#2196F3', background: 'rgba(33, 150, 243, 0.8)' },
      owo: { primary: '#FF9800', background: 'rgba(255, 152, 0, 0.8)' },
      pray: { primary: '#9C27B0', background: 'rgba(156, 39, 176, 0.8)' },
      curse: { primary: '#F44336', background: 'rgba(244, 67, 54, 0.8)' },
      daily: { primary: '#00BCD4', background: 'rgba(0, 188, 212, 0.8)' },
      sell: { primary: '#FFEB3B', background: 'rgba(255, 235, 59, 0.8)' },
      other: { primary: '#9E9E9E', background: 'rgba(158, 158, 158, 0.8)' }
    },
    resources: {
      cpu: { primary: '#FF5722', background: 'rgba(255, 87, 34, 0.8)' },
      memory: { primary: '#3F51B5', background: 'rgba(63, 81, 181, 0.8)' },
      latency: { primary: '#009688', background: 'rgba(0, 150, 136, 0.8)' }
    }
  }
};

// Initialize all charts when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Initialize charts
  initializeCharts();
  
  // Fetch initial data
  fetchStatisticsData();
  
  // Set up periodic data fetch
  setInterval(fetchStatisticsData, chartSettings.refreshInterval);
  
  // Initialize event listeners
  setupEventListeners();
});

// Initialize all chart objects
function initializeCharts() {
  // Income Distribution Chart
  if (document.getElementById('incomeDistributionChart')) {
    const incomeCtx = document.getElementById('incomeDistributionChart').getContext('2d');
    window.incomeDistributionChart = new Chart(incomeCtx, {
      type: 'doughnut',
      data: {
        labels: ['Hunt', 'Battle', 'Sell', 'Daily', 'Other'],
        datasets: [{
          data: [0, 0, 0, 0, 0],
          backgroundColor: [
            chartSettings.chartColors.commands.hunt.background,
            chartSettings.chartColors.commands.battle.background,
            chartSettings.chartColors.commands.sell.background,
            chartSettings.chartColors.commands.daily.background,
            chartSettings.chartColors.commands.other.background
          ],
          borderColor: [
            chartSettings.chartColors.commands.hunt.primary,
            chartSettings.chartColors.commands.battle.primary,
            chartSettings.chartColors.commands.sell.primary,
            chartSettings.chartColors.commands.daily.primary,
            chartSettings.chartColors.commands.other.primary
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: '#ddd'
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || '';
                const value = context.raw;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                return `${label}: ${formatNumber(value)} (${percentage}%)`;
              }
            }
          }
        }
      }
    });
  }
  
  // Command Success Rate Chart
  if (document.getElementById('commandSuccessChart')) {
    const successCtx = document.getElementById('commandSuccessChart').getContext('2d');
    window.commandSuccessChart = new Chart(successCtx, {
      type: 'bar',
      data: {
        labels: ['Hunt', 'Battle', 'OwO', 'Pray', 'Curse', 'Sell'],
        datasets: [{
          label: 'Success Rate (%)',
          data: [0, 0, 0, 0, 0, 0],
          backgroundColor: Object.values(chartSettings.chartColors.commands).map(c => c.background),
          borderColor: Object.values(chartSettings.chartColors.commands).map(c => c.primary),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `Success Rate: ${context.raw}%`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: '#aaa'
            }
          },
          x: {
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: '#aaa'
            }
          }
        }
      }
    });
  }
  
  // Hourly Earnings Chart
  if (document.getElementById('hourlyEarningsChart')) {
    const hourlyCtx = document.getElementById('hourlyEarningsChart').getContext('2d');
    window.hourlyEarningsChart = new Chart(hourlyCtx, {
      type: 'line',
      data: {
        labels: Array(24).fill().map((_, i) => `${i}:00`),
        datasets: [{
          label: 'Earnings per Hour',
          data: Array(24).fill(0),
          borderColor: chartSettings.chartColors.currency.primary,
          backgroundColor: chartSettings.chartColors.currency.background,
          fill: true,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            labels: {
              color: '#ddd'
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: ${formatNumber(context.raw)} cowoncy`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: '#aaa',
              callback: function(value) {
                return formatNumber(value);
              }
            }
          },
          x: {
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: '#aaa'
            }
          }
        }
      }
    });
  }
  
  // Resource Usage Chart
  if (document.getElementById('resourceUsageChart')) {
    const resourceCtx = document.getElementById('resourceUsageChart').getContext('2d');
    window.resourceUsageChart = new Chart(resourceCtx, {
      type: 'line',
      data: {
        labels: Array(15).fill('').map((_, i) => i),
        datasets: [
          {
            label: 'CPU (%)',
            data: Array(15).fill(0),
            borderColor: chartSettings.chartColors.resources.cpu.primary,
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0
          },
          {
            label: 'Memory (%)',
            data: Array(15).fill(0),
            borderColor: chartSettings.chartColors.resources.memory.primary,
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0
          },
          {
            label: 'Latency (ms)',
            data: Array(15).fill(0),
            borderColor: chartSettings.chartColors.resources.latency.primary,
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0,
            hidden: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            labels: {
              color: '#ddd'
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: '#aaa'
            }
          },
          x: {
            grid: {
              display: false
            },
            ticks: {
              display: false
            }
          }
        },
        animation: {
          duration: 0
        }
      }
    });
  }
}

// Fetch statistics data from the API
function fetchStatisticsData() {
  fetch('/api/stats')
    .then(response => response.json())
    .then(data => {
      // Store the data
      statsData = data;
      
      // Update history arrays
      updateDataHistory(data);
      
      // Update dashboard UI with the data
      updateDashboardStats(data);
      
      // Update charts with the new data
      updateAllCharts();
    })
    .catch(error => {
      console.error('Error fetching statistics:', error);
    });
}

// Update history arrays with new data
function updateDataHistory(data) {
  const now = new Date();
  statsHistory.timestamps.push(now);
  
  // Trim arrays if they exceed max length
  if (statsHistory.timestamps.length > chartSettings.historyLength) {
    statsHistory.timestamps.shift();
  }
  
  // Update currency history
  const totalCurrency = data.totalCurrency || 0;
  statsHistory.currency.push(totalCurrency);
  if (statsHistory.currency.length > chartSettings.historyLength) {
    statsHistory.currency.shift();
  }
  
  // Update command counts history
  const commands = data.commands || {};
  Object.keys(commands).forEach(cmd => {
    if (!statsHistory.commands[cmd]) {
      statsHistory.commands[cmd] = [];
    }
    
    const cmdCount = commands[cmd].count || 0;
    statsHistory.commands[cmd].push(cmdCount);
    
    if (statsHistory.commands[cmd].length > chartSettings.historyLength) {
      statsHistory.commands[cmd].shift();
    }
  });
  
  // Update resource usage history
  const system = data.system || {};
  const cpu = system.cpu || 0;
  const memory = system.memory || 0;
  const latency = system.latency || 0;
  
  statsHistory.resources.cpu.push(cpu);
  statsHistory.resources.memory.push(memory);
  statsHistory.resources.latency.push(latency);
  
  if (statsHistory.resources.cpu.length > chartSettings.historyLength) {
    statsHistory.resources.cpu.shift();
    statsHistory.resources.memory.shift();
    statsHistory.resources.latency.shift();
  }
  
  // Calculate hourly earnings (simplified for this implementation)
  const currentHour = now.getHours();
  if (!statsHistory.earnings.hourly[currentHour]) {
    statsHistory.earnings.hourly[currentHour] = 0;
  }
  
  // If we have at least two data points, calculate the difference
  if (statsHistory.currency.length >= 2) {
    const currencyDiff = statsHistory.currency[statsHistory.currency.length - 1] - 
                         statsHistory.currency[statsHistory.currency.length - 2];
    if (currencyDiff > 0) {
      statsHistory.earnings.hourly[currentHour] += currencyDiff;
    }
  }
}

// Update all charts with the latest data
function updateAllCharts() {
  updateIncomeDistributionChart();
  updateCommandSuccessChart();
  updateHourlyEarningsChart();
  updateResourceUsageChart();
}

// Update income distribution chart
function updateIncomeDistributionChart() {
  if (!window.incomeDistributionChart) return;
  
  // Calculate income from each source
  const income = {
    hunt: statsData.commands?.hunt?.currency || 0,
    battle: statsData.commands?.battle?.currency || 0,
    sell: statsData.commands?.sell?.currency || 0,
    daily: statsData.commands?.daily?.currency || 0,
    other: 0
  };
  
  // Calculate "other" category (all - known sources)
  const totalCurrency = statsData.totalCurrency || 0;
  const knownSources = income.hunt + income.battle + income.sell + income.daily;
  income.other = totalCurrency - knownSources > 0 ? totalCurrency - knownSources : 0;
  
  // Update chart data
  window.incomeDistributionChart.data.datasets[0].data = [
    income.hunt,
    income.battle,
    income.sell,
    income.daily,
    income.other
  ];
  
  window.incomeDistributionChart.update();
}

// Update command success rate chart
function updateCommandSuccessChart() {
  if (!window.commandSuccessChart) return;
  
  const commands = statsData.commands || {};
  const commandNames = ['hunt', 'battle', 'owo', 'pray', 'curse', 'sell'];
  
  const successRates = commandNames.map(cmd => {
    const command = commands[cmd] || {};
    const total = command.count || 0;
    const success = command.success || 0;
    return total > 0 ? Math.round((success / total) * 100) : 0;
  });
  
  window.commandSuccessChart.data.datasets[0].data = successRates;
  window.commandSuccessChart.update();
}

// Update hourly earnings chart
function updateHourlyEarningsChart() {
  if (!window.hourlyEarningsChart) return;
  
  window.hourlyEarningsChart.data.datasets[0].data = statsHistory.earnings.hourly;
  window.hourlyEarningsChart.update();
}

// Update resource usage chart
function updateResourceUsageChart() {
  if (!window.resourceUsageChart) return;
  
  window.resourceUsageChart.data.datasets[0].data = statsHistory.resources.cpu;
  window.resourceUsageChart.data.datasets[1].data = statsHistory.resources.memory;
  window.resourceUsageChart.data.datasets[2].data = statsHistory.resources.latency;
  
  window.resourceUsageChart.update();
}

// Update dashboard statistics display
function updateDashboardStats(data) {
  // Update overview stats
  updateElement('total-commands', formatNumber(data.totalCommands || 0));
  updateElement('total-currency', formatNumber(data.totalCurrency || 0));
  updateElement('runtime', formatUptime(data.system?.uptime || 0));
  
  // Calculate and update success rate
  let totalCommands = 0;
  let successfulCommands = 0;
  
  Object.values(data.commands || {}).forEach(cmd => {
    totalCommands += cmd.count || 0;
    successfulCommands += cmd.success || 0;
  });
  
  const successRate = totalCommands > 0 ? (successfulCommands / totalCommands) * 100 : 0;
  updateElement('success-rate', successRate.toFixed(1) + '%');
  
  // Update system health metrics
  updateElement('cpu-usage-value', (data.system?.cpu || 0) + '%');
  updateElement('memory-usage-value', (data.system?.memory || 0) + '%');
  updateElement('latency-value', (data.system?.latency || 0) + 'ms');
  
  // Update progress bars
  updateProgressBar('cpu-usage', data.system?.cpu || 0);
  updateProgressBar('memory-usage', data.system?.memory || 0);
  updateProgressBar('latency', Math.min(100, (data.system?.latency || 0) / 5));
  
  // Update battery if available
  if (data.system?.battery) {
    const batteryContainer = document.getElementById('battery-container');
    if (batteryContainer) {
      batteryContainer.style.display = 'flex';
      updateProgressBar('battery', data.system.battery);
      updateElement('battery-value', data.system.battery + '%');
    }
  }
  
  // Update trends/changes
  if (data.trends) {
    const currencyChange = data.trends.currency?.hourly || 0;
    const commandsChange = data.trends.commands?.hourly || 0;
    
    updateElement('currency-change', formatTrend(currencyChange));
    updateElement('commands-change', formatTrend(commandsChange));
    
    // Update trend classes
    updateTrendClass('currency-change', currencyChange);
    updateTrendClass('commands-change', commandsChange);
  }
  
  // Update command stats table
  updateCommandStatsTable(data.commands || {});
  
  // Update timeline
  updateTimeline(data.recentActivity || []);
  
  // Update pet statistics
  updatePetStats(data.pets || []);
}

// Update command stats table
function updateCommandStatsTable(commands) {
  const tableBody = document.querySelector('#command-stats-table tbody');
  if (!tableBody) return;
  
  // Clear existing rows
  tableBody.innerHTML = '';
  
  // Command names to display
  const commandNames = [
    'hunt', 'battle', 'owo', 'pray', 'curse', 'daily', 'sell'
  ];
  
  // Add rows for each command
  commandNames.forEach(cmdName => {
    const cmd = commands[cmdName] || {
      count: 0,
      success: 0,
      fail: 0,
      currency: 0,
      lastUsed: null
    };
    
    const row = document.createElement('tr');
    
    // Calculate success rate
    const successRate = cmd.count > 0 ? (cmd.success / cmd.count * 100).toFixed(1) : '0.0';
    
    // Format last used time
    const lastUsed = cmd.lastUsed ? formatTimeAgo(cmd.lastUsed) : 'Never';
    
    row.innerHTML = `
      <td>${cmdName.charAt(0).toUpperCase() + cmdName.slice(1)}</td>
      <td>${formatNumber(cmd.count)}</td>
      <td>${formatNumber(cmd.success)}</td>
      <td>${formatNumber(cmd.count - cmd.success)}</td>
      <td>${successRate}%</td>
      <td>${formatNumber(cmd.currency)}</td>
      <td>${lastUsed}</td>
    `;
    
    tableBody.appendChild(row);
  });
}

// Update the timeline with recent activity
function updateTimeline(activities) {
  const timelineContainer = document.getElementById('advanced-timeline');
  if (!timelineContainer) return;
  
  // Clear existing items
  timelineContainer.innerHTML = '';
  
  // Add timeline items
  activities.forEach(activity => {
    const timelineItem = document.createElement('div');
    timelineItem.className = `timeline-item-advanced event-${activity.type || 'info'}`;
    
    timelineItem.innerHTML = `
      <div class="timeline-time-advanced">${activity.time}</div>
      <div class="timeline-text-advanced">${activity.text}</div>
    `;
    
    timelineContainer.appendChild(timelineItem);
  });
  
  // If no activities, show a message
  if (activities.length === 0) {
    const emptyMessage = document.createElement('div');
    emptyMessage.className = 'timeline-item-advanced';
    emptyMessage.innerHTML = `
      <div class="timeline-text-advanced">No recent activity</div>
    `;
    timelineContainer.appendChild(emptyMessage);
  }
}

// Update pet statistics
function updatePetStats(pets) {
  const petContainer = document.getElementById('pet-stats-container');
  if (!petContainer) return;
  
  // Clear existing pets
  petContainer.innerHTML = '';
  
  // Add pet cards
  pets.forEach(pet => {
    const petCard = document.createElement('div');
    petCard.className = 'pet-card';
    
    // Calculate experience percentage
    const expPercentage = pet.maxExperience > 0 ? 
      (pet.experience / pet.maxExperience * 100).toFixed(1) : 0;
    
    petCard.innerHTML = `
      <div class="pet-name">${pet.name}</div>
      <div class="pet-level">Level ${pet.level}</div>
      <div class="pet-experience">
        <div class="pet-experience-progress" style="width: ${expPercentage}%"></div>
      </div>
      <div class="pet-stats">
        <span>ATK: ${pet.attack}</span>
        <span>DEF: ${pet.defense}</span>
      </div>
    `;
    
    petContainer.appendChild(petCard);
  });
  
  // If no pets, show a message
  if (pets.length === 0) {
    const emptyMessage = document.createElement('div');
    emptyMessage.className = 'pet-card';
    emptyMessage.innerHTML = `
      <div class="pet-name">No Pets</div>
      <div class="pet-level">Start hunting to collect pets!</div>
    `;
    petContainer.appendChild(emptyMessage);
  }
}

// Helper functions
function updateElement(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function updateProgressBar(id, value) {
  const progressBar = document.getElementById(id);
  if (progressBar) progressBar.style.width = `${value}%`;
}

function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function formatUptime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (hours > 24) {
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  }
  
  return `${hours}h ${minutes}m`;
}

// Set up event listeners for interactive elements
function setupEventListeners() {
  // Add event listeners for time period selectors if they exist
  const timeSelectors = document.querySelectorAll('.time-selector');
  timeSelectors.forEach(selector => {
    selector.addEventListener('click', function() {
      const period = this.dataset.period;
      const chartId = this.dataset.target;
      
      // Remove active class from all selectors in this group
      this.parentNode.querySelectorAll('.time-selector').forEach(el => {
        el.classList.remove('active');
      });
      
      // Add active class to the clicked selector
      this.classList.add('active');
      
      // Update chart based on selected time period
      if (period && chartId) {
        updateChartTimePeriod(chartId, period);
      }
    });
  });
}

// Update chart based on selected time period
function updateChartTimePeriod(chartId, period) {
  // This would update the chart to show data for the selected time period
  // Implementation depends on how you want to handle different time periods
  console.log(`Updating chart ${chartId} to show data for ${period} period`);
}

// Format trend value with + or - sign
function formatTrend(value) {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value}%`;
}

// Update the class of a trend element based on its value
function updateTrendClass(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.classList.remove('positive', 'negative');
    element.classList.add(value >= 0 ? 'positive' : 'negative');
  }
}

// Format time ago from a timestamp
function formatTimeAgo(timestamp) {
  if (!timestamp) return 'Never';
  
  try {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffSec = Math.floor(diffMs / 1000);
    
    if (diffSec < 60) return `${diffSec} sec ago`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)} min ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} hr ago`;
    return `${Math.floor(diffSec / 86400)} days ago`;
  } catch (e) {
    return 'Unknown';
  }
} 