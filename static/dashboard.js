/*
This file is part of owo-dusk.

Copyright (c) 2024-present EchoQuill

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
*/

// Demo data for charts and stats - would be replaced with real data from backend
const DEMO_DATA = {
  totalCommands: 12478,
  totalCurrency: 567832,
  runtime: "23h 45m",
  successRate: 99.7,
  
  currencyData: {
    labels: ['12:00', '14:00', '16:00', '18:00', '20:00', '22:00', '00:00', '02:00', '04:00', '06:00', '08:00', '10:00'],
    datasets: [
      {
        label: 'Currency Earned',
        data: [0, 12500, 19000, 32000, 39500, 52000, 67000, 73500, 78000, 86000, 92000, 106500],
        borderColor: '#FF79C3',
        backgroundColor: 'rgba(255, 121, 195, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }
    ]
  },
  
  commandsData: {
    labels: ['12:00', '14:00', '16:00', '18:00', '20:00', '22:00', '00:00', '02:00', '04:00', '06:00', '08:00', '10:00'],
    datasets: [
      {
        label: 'Hunt',
        data: [100, 120, 118, 125, 132, 126, 138, 140, 135, 142, 141, 145],
        borderColor: '#4CAF50',
        backgroundColor: 'rgba(76, 175, 80, 0.8)',
        borderWidth: 0,
        barPercentage: 0.6,
      },
      {
        label: 'Battle',
        data: [90, 115, 110, 122, 128, 118, 132, 135, 130, 138, 136, 140],
        borderColor: '#2196F3',
        backgroundColor: 'rgba(33, 150, 243, 0.8)',
        borderWidth: 0,
        barPercentage: 0.6,
      },
      {
        label: 'OwO',
        data: [80, 95, 93, 102, 110, 105, 112, 118, 115, 120, 118, 122],
        borderColor: '#FF9800',
        backgroundColor: 'rgba(255, 152, 0, 0.8)',
        borderWidth: 0,
        barPercentage: 0.6,
      }
    ]
  },
  
  timeline: [
    { time: '11:42:15', text: 'Successfully executed Hunt command', type: 'success' },
    { time: '11:39:22', text: 'Sold common animal for 402 cowoncy', type: 'success' },
    { time: '11:37:40', text: 'Successfully executed Battle command', type: 'success' },
    { time: '11:35:12', text: 'Successfully executed Hunt command', type: 'success' },
    { time: '11:32:33', text: 'Successfully executed OwO command', type: 'success' },
    { time: '11:29:51', text: 'Successfully executed Hunt command', type: 'success' },
    { time: '11:27:02', text: 'Detected rate limit, waiting 5 seconds', type: 'warning' },
    { time: '11:25:17', text: 'Successfully executed Battle command', type: 'success' },
    { time: '11:22:44', text: 'Successfully executed Hunt command', type: 'success' },
    { time: '11:20:01', text: 'Successfully executed OwO command', type: 'success' }
  ],
  
  events: [
    { time: '11:42:15', message: 'Earned 120 cowoncy from Hunt', type: 'success' },
    { time: '11:37:40', message: 'Earned 95 cowoncy from Battle', type: 'success' },
    { time: '11:27:02', message: 'Rate limit detected', type: 'warning' },
    { time: '11:15:33', message: 'Captcha detected', type: 'error' },
    { time: '11:10:05', message: 'Earned 85 cowoncy from Hunt', type: 'success' },
    { time: '11:05:47', message: 'Inventory full', type: 'info' },
    { time: '11:00:17', message: 'Bot started', type: 'info' }
  ],
  
  system: {
    cpu: 45,
    memory: 62,
    latency: 78,
    battery: 85
  }
};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
  // Set the stats overview values
  document.getElementById('total-commands').textContent = formatNumber(DEMO_DATA.totalCommands);
  document.getElementById('total-currency').textContent = formatNumber(DEMO_DATA.totalCurrency);
  document.getElementById('runtime').textContent = DEMO_DATA.runtime;
  document.getElementById('success-rate').textContent = DEMO_DATA.successRate + '%';
  
  // Initialize currency chart
  const currencyCtx = document.getElementById('currencyChart').getContext('2d');
  new Chart(currencyCtx, {
    type: 'line',
    data: DEMO_DATA.currencyData,
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
          mode: 'index',
          intersect: false,
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: '#aaa',
          }
        },
        y: {
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: '#aaa',
            callback: function(value) {
              return formatNumber(value);
            }
          }
        }
      }
    }
  });
  
  // Initialize commands chart
  const commandsCtx = document.getElementById('commandsChart').getContext('2d');
  new Chart(commandsCtx, {
    type: 'bar',
    data: DEMO_DATA.commandsData,
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
          mode: 'index',
          intersect: false,
        }
      },
      scales: {
        x: {
          stacked: true,
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: '#aaa',
          }
        },
        y: {
          stacked: true,
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
  
  // Populate timeline
  const timelineContent = document.getElementById('timeline-content');
  DEMO_DATA.timeline.forEach(item => {
    const timelineItem = document.createElement('div');
    timelineItem.className = 'timeline-item';
    timelineItem.innerHTML = `
      <div class="timeline-item-content">
        <div class="timeline-time">${item.time}</div>
        <div class="timeline-text">${item.text}</div>
      </div>
    `;
    timelineContent.appendChild(timelineItem);
  });
  
  // Populate events
  const eventsList = document.getElementById('events-list');
  DEMO_DATA.events.forEach(event => {
    const eventItem = document.createElement('div');
    eventItem.className = `event-item event-${event.type}`;
    eventItem.innerHTML = `
      <span class="event-time">${event.time}</span>
      <div class="event-message">${event.message}</div>
    `;
    eventsList.appendChild(eventItem);
  });
  
  // Set system health metrics
  document.getElementById('cpu-usage').style.width = `${DEMO_DATA.system.cpu}%`;
  document.querySelector('#cpu-usage').closest('.metric').querySelector('.metric-value').textContent = `${DEMO_DATA.system.cpu}%`;
  
  document.getElementById('memory-usage').style.width = `${DEMO_DATA.system.memory}%`;
  document.querySelector('#memory-usage').closest('.metric').querySelector('.metric-value').textContent = `${DEMO_DATA.system.memory}%`;
  
  document.getElementById('latency').style.width = `${DEMO_DATA.system.latency}%`;
  document.querySelector('#latency').closest('.metric').querySelector('.metric-value').textContent = `${DEMO_DATA.system.latency}ms`;
  
  document.getElementById('battery').style.width = `${DEMO_DATA.system.battery}%`;
  document.querySelector('#battery').closest('.metric').querySelector('.metric-value').textContent = `${DEMO_DATA.system.battery}%`;
  
  // Check if we need to hide battery (desktop environments)
  if (navigator.userAgent.match(/Windows|Mac|Linux/) && !navigator.userAgent.match(/Android|iPhone|iPad/)) {
    const batteryContainer = document.getElementById('battery-container');
    if (batteryContainer) {
      batteryContainer.style.display = 'none';
    }
  }
  
  // Simulate real-time updates
  setInterval(updateRandomStat, 3000);
});

// Helper functions
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function updateRandomStat() {
  // This would be replaced with real data from backend
  // For now, let's just simulate random updates
  const rand = Math.floor(Math.random() * 4);
  
  if (rand === 0) {
    const newCommands = DEMO_DATA.totalCommands + Math.floor(Math.random() * 5);
    DEMO_DATA.totalCommands = newCommands;
    document.getElementById('total-commands').textContent = formatNumber(newCommands);
    
    // Add new timeline item
    const timelineContent = document.getElementById('timeline-content');
    const now = new Date();
    const timeString = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    
    const commands = ['Hunt', 'Battle', 'OwO'];
    const commandType = commands[Math.floor(Math.random() * commands.length)];
    
    const timelineItem = document.createElement('div');
    timelineItem.className = 'timeline-item';
    timelineItem.innerHTML = `
      <div class="timeline-item-content">
        <div class="timeline-time">${timeString}</div>
        <div class="timeline-text">Successfully executed ${commandType} command</div>
      </div>
    `;
    timelineContent.insertBefore(timelineItem, timelineContent.firstChild);
    
    // Remove last item if more than 10
    if (timelineContent.children.length > 10) {
      timelineContent.removeChild(timelineContent.lastChild);
    }
  } else if (rand === 1) {
    const earnings = Math.floor(Math.random() * 120);
    const newCurrency = DEMO_DATA.totalCurrency + earnings;
    DEMO_DATA.totalCurrency = newCurrency;
    document.getElementById('total-currency').textContent = formatNumber(newCurrency);
    
    // Add new event
    const eventsList = document.getElementById('events-list');
    const now = new Date();
    const timeString = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    
    const commands = ['Hunt', 'Battle', 'OwO'];
    const commandType = commands[Math.floor(Math.random() * commands.length)];
    
    const eventItem = document.createElement('div');
    eventItem.className = 'event-item event-success';
    eventItem.innerHTML = `
      <span class="event-time">${timeString}</span>
      <div class="event-message">Earned ${earnings} cowoncy from ${commandType}</div>
    `;
    eventsList.insertBefore(eventItem, eventsList.firstChild);
    
    // Remove last item if more than 7
    if (eventsList.children.length > 7) {
      eventsList.removeChild(eventsList.lastChild);
    }
  }
  
  // Update system stats randomly
  const cpuChange = Math.random() * 10 - 5;
  let newCpu = DEMO_DATA.system.cpu + cpuChange;
  newCpu = Math.max(5, Math.min(95, newCpu));
  DEMO_DATA.system.cpu = Math.round(newCpu);
  document.getElementById('cpu-usage').style.width = `${DEMO_DATA.system.cpu}%`;
  document.querySelector('#cpu-usage').closest('.metric').querySelector('.metric-value').textContent = `${DEMO_DATA.system.cpu}%`;
  
  const memChange = Math.random() * 8 - 4;
  let newMem = DEMO_DATA.system.memory + memChange;
  newMem = Math.max(20, Math.min(90, newMem));
  DEMO_DATA.system.memory = Math.round(newMem);
  document.getElementById('memory-usage').style.width = `${DEMO_DATA.system.memory}%`;
  document.querySelector('#memory-usage').closest('.metric').querySelector('.metric-value').textContent = `${DEMO_DATA.system.memory}%`;
  
  const latencyChange = Math.random() * 15 - 7;
  let newLatency = DEMO_DATA.system.latency + latencyChange;
  newLatency = Math.max(30, Math.min(150, newLatency));
  DEMO_DATA.system.latency = Math.round(newLatency);
  document.getElementById('latency').style.width = `${Math.min(100, DEMO_DATA.system.latency / 1.5)}%`;
  document.querySelector('#latency').closest('.metric').querySelector('.metric-value').textContent = `${DEMO_DATA.system.latency}ms`;
  
  // Only update battery occasionally
  if (Math.random() > 0.7) {
    const batteryChange = Math.random() > 0.7 ? -1 : 0;
    let newBattery = DEMO_DATA.system.battery + batteryChange;
    newBattery = Math.max(5, Math.min(100, newBattery));
    DEMO_DATA.system.battery = Math.round(newBattery);
    const batteryElement = document.getElementById('battery');
    if (batteryElement) {
      batteryElement.style.width = `${DEMO_DATA.system.battery}%`;
      document.querySelector('#battery').closest('.metric').querySelector('.metric-value').textContent = `${DEMO_DATA.system.battery}%`;
    }
  }
} 