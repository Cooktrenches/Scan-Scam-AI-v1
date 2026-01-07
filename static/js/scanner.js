// Scanner JavaScript

// Function to generate social links
function generateSocialLinks(metadata) {
    if (!metadata) return '';

    const links = [];

    // Website first (with globe icon)
    if (metadata.website) {
        links.push(`<a href="${metadata.website}" target="_blank" class="social-link" title="Website">
            <i class="fas fa-globe" style="color: #00ff88; font-size: 18px;"></i>
        </a>`);
    }

    // X/Twitter second (white color)
    if (metadata.twitter) {
        links.push(`<a href="${metadata.twitter}" target="_blank" class="social-link" title="Twitter/X">
            <span style="color: #ffffff; font-size: 20px; font-weight: bold;">𝕏</span>
        </a>`);
    }

    // Telegram last (with real Telegram logo)
    if (metadata.telegram) {
        links.push(`<a href="${metadata.telegram}" target="_blank" class="social-link" title="Telegram">
            <i class="fab fa-telegram" style="color: #0088cc; font-size: 18px;"></i>
        </a>`);
    }

    if (links.length === 0) {
        return '<p style="color: #ff4444; font-size: 12px; margin: 8px 0;">No social links found</p>';
    }

    return `
        <div style="display: flex; gap: 12px; margin: 8px 0; align-items: center;">
            ${links.join('')}
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', () => {
    const scanForm = document.getElementById('scanForm');
    const mintAddressInput = document.getElementById('mintAddress');
    const scanButton = document.getElementById('scanButton');
    const buttonText = document.getElementById('buttonText');
    const buttonLoader = document.getElementById('buttonLoader');
    const resultsSection = document.getElementById('results');
    const errorSection = document.getElementById('error');
    const statusValue = document.getElementById('statusValue');

    scanForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const mintAddress = mintAddressInput.value.trim();

        if (!mintAddress) {
            showError('Please enter a token contract address');
            return;
        }

        // Validate address format
        if (mintAddress.length < 32 || mintAddress.length > 44) {
            showError('Invalid Solana address format');
            return;
        }

        // Start scan
        startScan();

        // Start progress simulation
        const progressInterval = simulateProgress();

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mint_address: mintAddress
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Scan failed');
            }

            // Check if response contains an error (even with 200 status)
            if (data.error) {
                throw new Error(data.error);
            }

            // Complete progress bar to 100%
            progressFill.style.width = '100%';

            displayResults(data);

            // Update scan counter from backend
            updateScanCount();

        } catch (error) {
            showError(error.message);
        } finally {
            clearInterval(progressInterval);
            stopScan();
        }
    });

    // Get progress elements
    const progressSection = document.getElementById('progressSection');
    const progressFill = document.getElementById('progressFill');
    const progressStepsContainer = document.getElementById('progressSteps');

    // Progress steps configuration
    const steps = [
        { text: 'Fetching token data...', duration: 3000, icon: '[>]' },
        { text: 'Analyzing liquidity & market cap...', duration: 3500, icon: '[$]' },
        { text: 'Checking mint/freeze authority...', duration: 2500, icon: '[#]' },
        { text: 'Analyzing holder distribution...', duration: 4000, icon: '[*]' },
        { text: 'Detecting snipers & insider trading...', duration: 3500, icon: '[^]' },
        { text: 'Checking for wash trading...', duration: 3000, icon: '[=]' },
        { text: 'Analyzing pump & dump patterns...', duration: 3000, icon: '[~]' },
        { text: 'Calculating risk score...', duration: 2500, icon: '[!]' }
    ];

    function simulateProgress() {
        // Update status
        if (statusValue) statusValue.textContent = 'SCANNING';

        // Show progress section
        progressSection.classList.add('active');
        progressSection.style.display = 'block';
        progressStepsContainer.innerHTML = '';

        // Create step elements
        steps.forEach((step, index) => {
            const stepEl = document.createElement('div');
            stepEl.className = 'progress-step';
            stepEl.id = `step-${index}`;
            stepEl.innerHTML = `
                <span class="progress-step-icon">${step.icon}</span>
                <span class="progress-step-text">${step.text}</span>
            `;
            progressStepsContainer.appendChild(stepEl);
        });

        let currentStep = 0;
        let currentProgress = 0;

        // Mark first step as active
        document.getElementById(`step-0`).classList.add('active');

        const interval = setInterval(() => {
            if (currentStep >= steps.length) {
                currentProgress = 100;
                progressFill.style.width = '100%';
                clearInterval(interval);
                return;
            }

            // Update progress
            const progressPerStep = 100 / steps.length;
            const targetProgress = Math.min((currentStep + 1) * progressPerStep, 100);

            if (currentProgress < targetProgress) {
                currentProgress += 1.2;  // Progression équilibrée
                if (currentProgress > targetProgress) currentProgress = targetProgress;
                progressFill.style.width = currentProgress + '%';
            } else {
                // Mark current step as completed
                const currentStepEl = document.getElementById(`step-${currentStep}`);
                if (currentStepEl) {
                    currentStepEl.classList.remove('active');
                    currentStepEl.classList.add('completed');
                }

                // Move to next step
                currentStep++;
                if (currentStep < steps.length) {
                    const nextStepEl = document.getElementById(`step-${currentStep}`);
                    if (nextStepEl) {
                        nextStepEl.classList.add('active');
                    }
                }
            }
        }, 100);  // Interval plus rapide (200ms -> 100ms) pour animation plus fluide

        return interval;
    }

    function startScan() {
        scanButton.disabled = true;
        buttonText.style.display = 'none';
        resultsSection.style.display = 'none';
        errorSection.style.display = 'none';
    }

    function stopScan() {
        scanButton.disabled = false;
        buttonText.style.display = 'inline';
        progressSection.style.display = 'none';
        if (statusValue) statusValue.textContent = 'READY';
    }

    function showError(message) {
        errorSection.classList.add('active');
        errorSection.style.display = 'block';
        errorSection.querySelector('.error-message').textContent = `[X] Error: ${message}`;
        resultsSection.style.display = 'none';
        progressSection.style.display = 'none';
        if (statusValue) statusValue.textContent = 'ERROR';
    }

    function displayResults(data) {
        errorSection.style.display = 'none';
        errorSection.classList.remove('active');

        // Check if data has expected structure
        if (!data || !data.risk_assessment) {
            showError('Invalid response from server: ' + JSON.stringify(data));
            return;
        }

        const riskLevel = data.risk_assessment.risk_level.toLowerCase();
        const riskScore = data.risk_assessment.overall_score;

        const html = `
            <div class="result-header">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-items: start;">
                    <div>
                        <h2 class="token-name">
                            ${data.token_info.name} (${data.token_info.symbol})
                        </h2>
                        ${generateSocialLinks(data.metadata)}
                        <p class="token-address">Contract: ${data.mint_address}</p>
                        <p style="color: #ff8c42; font-weight: bold; margin-top: 12px;">[T] Token Age: <span style="color: #e8e8e8; font-weight: normal;">${data.token_info.age}</span></p>
                    </div>

                    ${data.detailed_analysis && data.detailed_analysis.authority_analysis ? `
                        <div style="padding-top: 8px;">
                            <p style="color: #ff8c42; font-weight: bold; margin-bottom: 12px;">[#] Token Security Status (CRITICAL)</p>
                            <p style="color: #a0a0a0; margin-bottom: 4px;">Mint Authority: <span style="color: ${data.detailed_analysis.authority_analysis.mint_authority_renounced ? '#00ff88' : '#ff0000'}; font-weight: bold;">
                                ${data.detailed_analysis.authority_analysis.mint_authority_renounced ? '[OK] RENOUNCED' : '[X] NOT RENOUNCED'}
                            </span></p>
                            <p style="color: #a0a0a0;">Freeze Authority: <span style="color: ${data.detailed_analysis.authority_analysis.freeze_authority_renounced ? '#00ff88' : '#ff0000'}; font-weight: bold;">
                                ${data.detailed_analysis.authority_analysis.freeze_authority_renounced ? '[OK] RENOUNCED' : '[X] NOT RENOUNCED'}
                            </span></p>
                        </div>
                    ` : ''}
                </div>
            </div>

            ${data.ml_prediction && data.ml_prediction.enabled ? `
                <div class="ml-prediction-banner" style="background: linear-gradient(135deg, #1a0a0a 0%, #2e1a0a 100%); border: 2px solid #ff8c42; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 0 20px rgba(255, 140, 66, 0.3);">
                    <h3 style="color: #ff8c42; margin-bottom: 15px; font-size: 18px;">[AI] Machine Learning Prediction</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <p style="color: #a0a0a0; margin-bottom: 8px;">AI Score:</p>
                            <p style="color: #ff8c42; font-size: 32px; font-weight: bold;">
                                ${data.ml_prediction.score}/100
                            </p>
                            <p style="color: #808080; font-size: 12px; margin-top: 4px;">
                                Confidence: ${data.ml_prediction.confidence.toFixed(1)}%
                            </p>
                        </div>
                        <div></div>
                    </div>
                    <div style="margin-top: 15px;">
                        <p style="color: #a0a0a0; margin-bottom: 8px;">Probabilities:</p>
                        <div style="display: flex; gap: 15px;">
                            ${Object.entries(data.ml_prediction.probabilities).map(([className, prob]) => `
                                <div style="flex: 1;">
                                    <span style="color: ${className === 'RUG' ? '#ff4444' : '#00ff88'};">${className}: ${prob.toFixed(1)}%</span>
                                    <div style="background: #1a1a2e; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 4px;">
                                        <div style="background: ${className === 'RUG' ? '#ff4444' : '#00ff88'}; height: 100%; width: ${prob}%;"></div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            ` : ''}

            ${data.risk_assessment.confidence ? `
                <div class="confidence-banner" style="background: linear-gradient(135deg, ${
                    data.risk_assessment.confidence.level === 'LOW' ? '#1a0a0a 0%, #2e1616 100%' :
                    data.risk_assessment.confidence.level === 'MEDIUM' ? '#1a1a0a 0%, #2e2616 100%' :
                    '#1a2a1a 0%, #1e3a1e 100%'
                }); border: 2px solid ${
                    data.risk_assessment.confidence.level === 'LOW' ? '#ff3333' :
                    data.risk_assessment.confidence.level === 'MEDIUM' ? '#ffaa00' :
                    '#00ff88'
                }; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 0 20px ${
                    data.risk_assessment.confidence.level === 'LOW' ? 'rgba(255, 51, 51, 0.3)' :
                    data.risk_assessment.confidence.level === 'MEDIUM' ? 'rgba(255, 170, 0, 0.3)' :
                    'rgba(0, 255, 136, 0.2)'
                };">
                    <h3 style="color: ${
                        data.risk_assessment.confidence.level === 'LOW' ? '#ff3333' :
                        data.risk_assessment.confidence.level === 'MEDIUM' ? '#ffaa00' :
                        '#00ff88'
                    }; margin-bottom: 15px; font-size: 18px;">[i] Analysis Confidence</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <p style="color: #a0a0a0; margin-bottom: 8px;">Confidence Level:</p>
                            <p style="color: ${
                                data.risk_assessment.confidence.level === 'VERY HIGH' ? '#00ff88' :
                                data.risk_assessment.confidence.level === 'HIGH' ? '#00ff88' :
                                data.risk_assessment.confidence.level === 'MEDIUM' ? '#ffaa00' :
                                '#ff3333'
                            }; font-size: 20px; font-weight: bold;">
                                ${data.risk_assessment.confidence.level}
                            </p>
                        </div>
                        <div>
                            <p style="color: #a0a0a0; margin-bottom: 8px;">Confidence Score:</p>
                            <p style="color: ${
                                data.risk_assessment.confidence.level === 'LOW' ? '#ff3333' :
                                data.risk_assessment.confidence.level === 'MEDIUM' ? '#ffaa00' :
                                '#00ff88'
                            }; font-size: 20px; font-weight: bold;">
                                ${data.risk_assessment.confidence.score}/100
                            </p>
                            <div style="background: #0a0a0a; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 8px;">
                                <div style="background: ${
                                    data.risk_assessment.confidence.level === 'LOW' ? 'linear-gradient(90deg, #ff3333, #ff6666)' :
                                    data.risk_assessment.confidence.level === 'MEDIUM' ? 'linear-gradient(90deg, #ffaa00, #ffd700)' :
                                    'linear-gradient(90deg, #00ff88, #00d9ff)'
                                }; height: 100%; width: ${data.risk_assessment.confidence.score}%; transition: width 1s ease;"></div>
                            </div>
                        </div>
                    </div>
                    ${data.risk_assessment.confidence.factors && data.risk_assessment.confidence.factors.length > 0 ? `
                        <div style="margin-top: 15px; border-top: 1px solid ${
                            data.risk_assessment.confidence.level === 'LOW' ? 'rgba(255, 51, 51, 0.2)' :
                            data.risk_assessment.confidence.level === 'MEDIUM' ? 'rgba(255, 170, 0, 0.2)' :
                            'rgba(0, 255, 136, 0.2)'
                        }; padding-top: 15px;">
                            <p style="color: #a0a0a0; margin-bottom: 8px; font-size: 14px;">Factors Affecting Confidence:</p>
                            <ul style="list-style: none; padding: 0; margin: 0;">
                                ${data.risk_assessment.confidence.factors.map(factor => `
                                    <li style="color: ${factor.startsWith('[+]') ? '#00ff88' : factor.startsWith('[!]') ? '#ff9900' : '#a0a0a0'}; font-size: 12px; margin-bottom: 4px; padding-left: 8px;">
                                        ${factor}
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            ` : ''}

            <div class="info-grid">
                <div class="info-card">
                    <h3>[$] Market Data</h3>
                    <div class="info-item">
                        <span class="info-label">Market Cap:</span>
                        <span class="info-value">${data.market_data.market_cap}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Liquidity:</span>
                        <span class="info-value">${data.market_data.liquidity}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Price:</span>
                        <span class="info-value">${data.market_data.price}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">24h Volume:</span>
                        <span class="info-value">${data.market_data.volume_24h}</span>
                    </div>
                </div>

                <div class="info-card">
                    <h3>[*] Holder Stats</h3>
                    <div class="info-item">
                        <span class="info-label">Total Holders:</span>
                        <span class="info-value">${data.holder_stats.total_holders}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Top Holder:</span>
                        <span class="info-value">${data.holder_stats.top_holder_percentage}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Top 10:</span>
                        <span class="info-value">${data.holder_stats.top_10_percentage}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Fresh Wallets (Top 10):</span>
                        <span class="info-value" style="color: ${data.holder_stats.fresh_wallets_top10 > 5 ? '#ff4444' : '#00ff88'}">${data.holder_stats.fresh_wallets_top10}</span>
                    </div>
                </div>

                <div class="info-card">
                    <h3>[=] Component Scores</h3>
                    <div class="info-item">
                        <span class="info-label">Liquidity:</span>
                        <span class="info-value">${data.risk_assessment.component_scores.liquidity}/100</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Creator History:</span>
                        <span class="info-value">${data.risk_assessment.component_scores.creator_history}/100</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Social Presence:</span>
                        <span class="info-value">${data.risk_assessment.component_scores.social_presence}/100</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Wallet Analysis:</span>
                        <span class="info-value">${data.risk_assessment.component_scores.wallet_analysis}/100</span>
                    </div>
                </div>

                <div class="info-card">
                    <h3>[>] Detection Results</h3>
                    <div class="info-item">
                        <span class="info-label">Sniper Detection:</span>
                        <span class="info-value">${data.risk_assessment.component_scores.sniper_detection}/100</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Volume Analysis:</span>
                        <span class="info-value">${data.risk_assessment.component_scores.volume_analysis}/100</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Pump & Dump:</span>
                        <span class="info-value">${data.risk_assessment.component_scores.pump_dump}/100</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Distribution:</span>
                        <span class="info-value">${data.risk_assessment.component_scores.distribution}/100</span>
                    </div>
                </div>
            </div>

            ${data.detailed_analysis ? `
                <div class="info-grid">
                    <div class="info-card">
                        <h3>[^] Sniper Analysis</h3>
                        <div class="info-item">
                            <span class="info-label">Instant Snipers (3s):</span>
                            <span class="info-value" style="color: ${data.detailed_analysis.sniper_analysis.instant_snipers > 0 ? '#ff4444' : '#00ff88'}">${data.detailed_analysis.sniper_analysis.instant_snipers} txs (${data.detailed_analysis.sniper_analysis.instant_sniper_percentage})</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Total Snipers (10s):</span>
                            <span class="info-value">${data.detailed_analysis.sniper_analysis.total_snipers} txs (${data.detailed_analysis.sniper_analysis.sniper_percentage})</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Coordinated Buying:</span>
                            <span class="info-value" style="color: ${data.detailed_analysis.sniper_analysis.coordinated_buying ? '#ff4444' : '#00ff88'}">${data.detailed_analysis.sniper_analysis.coordinated_buying ? 'YES [!]' : 'NO [OK]'}</span>
                        </div>
                    </div>

                    <div class="info-card">
                        <h3>[=] Volume Analysis</h3>
                        <div class="info-item">
                            <span class="info-label">Wash Trading:</span>
                            <span class="info-value" style="color: ${data.detailed_analysis.volume_analysis.is_wash_trading ? '#ff4444' : '#00ff88'}">${data.detailed_analysis.volume_analysis.is_wash_trading ? 'DETECTED [!!]' : 'NOT DETECTED [OK]'}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Fake Volume:</span>
                            <span class="info-value" style="color: ${data.detailed_analysis.volume_analysis.is_fake_volume ? '#ff4444' : '#00ff88'}">${data.detailed_analysis.volume_analysis.is_fake_volume ? 'DETECTED [!!]' : 'NOT DETECTED [OK]'}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Vol/MCap Ratio:</span>
                            <span class="info-value">${data.detailed_analysis.volume_analysis.volume_to_mcap_ratio}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Buy Volume %:</span>
                            <span class="info-value">${data.detailed_analysis.volume_analysis.buy_volume_percentage}</span>
                        </div>
                    </div>

                    <div class="info-card">
                        <h3>[~] Pump & Dump</h3>
                        <div class="info-item">
                            <span class="info-label">Pattern Detected:</span>
                            <span class="info-value" style="color: ${data.detailed_analysis.pump_dump_analysis.is_pump_dump ? '#ff4444' : '#00ff88'}">${data.detailed_analysis.pump_dump_analysis.is_pump_dump ? 'YES [!!]' : 'NO [OK]'}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Volatility:</span>
                            <span class="info-value">${data.detailed_analysis.pump_dump_analysis.price_volatility}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Max Price Spike:</span>
                            <span class="info-value">${data.detailed_analysis.pump_dump_analysis.max_price_spike}</span>
                        </div>
                    </div>

                    <div class="info-card">
                        <h3>[W] Wallet Analysis</h3>
                        <div class="info-item">
                            <span class="info-label">Fresh Wallets:</span>
                            <span class="info-value" style="color: ${parseFloat(data.detailed_analysis.wallet_analysis.fresh_wallet_percentage) > 40 ? '#ff4444' : '#00ff88'}">${data.detailed_analysis.wallet_analysis.fresh_wallet_percentage}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Dev Wallets:</span>
                            <span class="info-value">${data.detailed_analysis.wallet_analysis.suspected_dev_wallets}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Low Activity:</span>
                            <span class="info-value">${data.detailed_analysis.wallet_analysis.low_activity_wallets}</span>
                        </div>
                    </div>
                </div>
            ` : ''}

            ${data.red_flags && data.red_flags.length > 0 ? `
                <div class="analysis-section">
                    <div class="analysis-title">[!] Red Flags Detected</div>
                    <div class="red-flags">
                        ${data.red_flags.map(flag => `<div class="flag-item">${flag}</div>`).join('')}
                    </div>
                </div>
            ` : ''}

            ${data.recommendations && data.recommendations.length > 0 ? `
                <div class="analysis-section">
                    <div class="analysis-title">[i] Recommendations</div>
                    <div class="red-flags">
                        ${data.recommendations.map(rec => `<div class="flag-item warning">${rec}</div>`).join('')}
                    </div>
                </div>
            ` : ''}
        `;

        resultsSection.innerHTML = html;
        resultsSection.classList.add('active');
        resultsSection.style.display = 'block';

        // Update status
        if (statusValue) statusValue.textContent = 'COMPLETE';

        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }

    function getRiskSymbol(riskLevel) {
        const level = riskLevel.toLowerCase();
        switch (level) {
            // New safety-based levels
            case 'safe':
                return '[OK]';
            case 'moderate':
                return '[!]';
            case 'danger':
                return '[X]';
            // Legacy risk-based levels (for backwards compatibility)
            case 'low':
                return '[X]'; // Low risk = safe
            case 'medium':
                return '[!]';
            case 'high':
            case 'extreme':
                return '[OK]'; // High risk = danger
            default:
                return '[?]';
        }
    }

    // Update scan count from backend
    async function updateScanCount() {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                const stats = await response.json();
                const scanCountElement = document.getElementById('scanCount');
                if (scanCountElement) {
                    scanCountElement.textContent = stats.total_scans || 0;
                }
            }
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }
});
