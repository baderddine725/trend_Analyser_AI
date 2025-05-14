// Initialize charts and data
let trendChart;
let platformChart;

// Fetch and display trends
async function fetchTrends() {
    try {
        const response = await fetch('/api/trends');
        const data = await response.json();
        updateCharts(data);
    } catch (error) {
        console.error('Error fetching trends:', error);
    }
}

// Update charts with trend data
function updateCharts(data) {
    // Trending topics chart
    const ctx1 = document.getElementById('trendChart').getContext('2d');
    if (trendChart) {
        trendChart.destroy();
    }
    trendChart = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: Object.keys(data.top_keywords),
            datasets: [{
                label: 'Trend Frequency',
                data: Object.values(data.top_keywords),
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Platform comparison chart
    const ctx2 = document.getElementById('platformChart').getContext('2d');
    if (platformChart) {
        platformChart.destroy();
    }
    platformChart = new Chart(ctx2, {
        type: 'pie',
        data: {
            labels: ['TikTok', 'Twitter'],
            datasets: [{
                data: [
                    data.platform_comparison.tiktok,
                    data.platform_comparison.twitter
                ],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(54, 162, 235, 0.5)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true
        }
    });
}

// Handle content generation form
document.getElementById('contentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const topic = document.getElementById('contentTopic').value;
    const type = document.getElementById('contentType').value;

    try {
        const response = await fetch('/api/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ topic, type })
        });
        const data = await response.json();
        displayContentSuggestions(data);

        // Fetch recommendations for the topic
        const recResponse = await fetch(`/api/recommendations?topic=${encodeURIComponent(topic)}`);
        const recData = await recResponse.json();
        displayRecommendations(recData);
    } catch (error) {
        console.error('Error generating content:', error);
    }
});

// Display content suggestions
function displayContentSuggestions(data) {
    const container = document.getElementById('contentSuggestions');
    container.innerHTML = `
        <div class="alert alert-success mt-3">
            <h6>Generated Content Idea:</h6>
            <p>${data.content}</p>
            <h6>Suggestions:</h6>
            <ul>
                ${data.suggestions.map(s => `<li>${s}</li>`).join('')}
            </ul>
        </div>
    `;
}

// Display recommendations
function displayRecommendations(data) {
    const container = document.getElementById('recommendations');
    container.innerHTML = `
        <div class="mb-3">
            <h6>Recommended Hashtags:</h6>
            <div class="d-flex flex-wrap gap-2">
                ${data.hashtags.map(tag => `
                    <span class="badge bg-primary">${tag}</span>
                `).join('')}
            </div>
        </div>
        <div class="mb-3">
            <h6>Best Posting Times:</h6>
            <p>${data.best_posting_times.join(', ')}</p>
        </div>
        <div class="mb-3">
            <h6>Content Ideas:</h6>
            <div class="list-group">
                ${data.video_ideas.map(idea => `
                    <div class="list-group-item">
                        <h6>${idea.title}</h6>
                        <p class="mb-1">Format: ${idea.format}</p>
                        <small class="text-muted">Expected engagement: ${idea.estimated_engagement}</small>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

async function fetchTrendPredictions() {
    try {
        const response = await fetch('/api/trend-predictions');
        const data = await response.json();
        displayTrendPredictions(data);
    } catch (error) {
        console.error('Error fetching trend predictions:', error);
    }
}

function displayTrendPredictions(data) {
    const container = document.getElementById('recommendations');
    if (!container) return;

    let predictionsHtml = '<div class="mb-4"><h5>Trend Predictions</h5>';

    for (const [topic, predictions] of Object.entries(data.predictions)) {
        predictionsHtml += `
            <div class="card mb-3">
                <div class="card-header">
                    <h6>${topic}</h6>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Predicted Views</th>
                                    <th>Range</th>
                                    <th>Confidence</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${predictions.map(pred => `
                                    <tr>
                                        <td>${pred.date}</td>
                                        <td>${pred.predicted_views.toLocaleString()}</td>
                                        <td>
                                            <small class="text-muted">
                                                ${pred.lower_bound.toLocaleString()} - ${pred.upper_bound.toLocaleString()}
                                            </small>
                                        </td>
                                        <td>
                                            <div class="progress">
                                                <div class="progress-bar ${pred.confidence > 70 ? 'bg-success' : pred.confidence > 40 ? 'bg-warning' : 'bg-danger'}" 
                                                    role="progressbar" 
                                                    style="width: ${pred.confidence}%" 
                                                    aria-valuenow="${pred.confidence}" 
                                                    aria-valuemin="0" 
                                                    aria-valuemax="100">
                                                    ${pred.confidence}%
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }

    predictionsHtml += `
        <small class="text-muted">Last updated: ${data.updated_at}</small>
    </div>`;

    container.innerHTML = predictionsHtml;
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    feather.replace();
    fetchTrends();
    fetchTrendPredictions();
    setInterval(fetchTrends, 300000); // Refresh every 5 minutes
    setInterval(fetchTrendPredictions, 300000); // Refresh predictions every 5 minutes
});
