/* ==========================================
   GitGrade - Frontend JavaScript
   ========================================== */

// API Base URL
const API_BASE = '';

// State
let currentReport = null;
let currentAssets = [];

// Advanced Options State
let selectedMode = 'fast';
let selectedPersona = 'mentor';

// Grade percentages for bar fill
const GRADE_PERCENTAGES = {
    'A': 100,
    'B': 80,
    'C': 60,
    'D': 40,
    'F': 20
};

// ==========================================
// Advanced Options Functions
// ==========================================

function toggleAdvancedOptions() {
    const panel = document.getElementById('advancedPanel');
    const arrow = document.getElementById('toggleArrow');
    
    panel.classList.toggle('hidden');
    arrow.classList.toggle('rotated');
}

function setMode(mode) {
    selectedMode = mode;
    
    // Update UI
    document.querySelectorAll('.option-btn[data-mode]').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.option-btn[data-mode="${mode}"]`).classList.add('active');
}

function setPersona(persona) {
    selectedPersona = persona;
    
    // Update UI
    document.querySelectorAll('.persona-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.persona-btn[data-persona="${persona}"]`).classList.add('active');
}

// ==========================================
// Helper Functions for 5 Key Areas
// ==========================================

// Convert numeric score to letter grade
function scoreToGrade(score) {
    if (score >= 90) return 'A';
    if (score >= 75) return 'B';
    if (score >= 60) return 'C';
    if (score >= 40) return 'D';
    return 'F';
}

// Estimate commit rating from overall score if not provided
function estimateCommitRating(overallScore) {
    // Commits typically correlate with overall quality
    if (overallScore >= 85) return 'A';
    if (overallScore >= 70) return 'B';
    if (overallScore >= 55) return 'C';
    if (overallScore >= 35) return 'D';
    return 'F';
}

// Estimate real-world value rating from metrics
function estimateValueRating(overallScore, metrics) {
    // Value combines uniqueness, completeness, and professionalism
    const structScore = GRADE_PERCENTAGES[metrics.structure_rating] || 60;
    const docsScore = GRADE_PERCENTAGES[metrics.docs_rating] || 60;
    const testScore = GRADE_PERCENTAGES[metrics.test_rating] || 60;
    
    // Weight: structure 30%, docs 40%, tests 30%
    const valueScore = (structScore * 0.3) + (docsScore * 0.4) + (testScore * 0.3);
    return scoreToGrade(valueScore);
}

// File type icons
const FILE_ICONS = {
    'folder': '📁',
    'js': '📜',
    'ts': '📘',
    'py': '🐍',
    'json': '📋',
    'md': '📝',
    'html': '🌐',
    'css': '🎨',
    'default': '📄'
};

// ==========================================
// Main Functions
// ==========================================

function setExample(url) {
    document.getElementById('repoUrl').value = url;
}

async function analyzeRepo() {
    const urlInput = document.getElementById('repoUrl');
    const deployInput = document.getElementById('deployUrl');
    const url = urlInput.value.trim();
    const deployUrl = deployInput ? deployInput.value.trim() : '';
    
    if (!url) {
        shakeInput(urlInput);
        return;
    }
    
    if (!isValidGitHubUrl(url)) {
        shakeInput(urlInput);
        alert('Please enter a valid GitHub repository URL');
        return;
    }
    
    // Show progress, hide input and results
    showSection('progressSection');
    hideSection('inputSection');
    hideSection('resultsSection');
    
    // Update progress message based on mode
    updateProgressForMode(selectedMode);
    
    // Start progress animation
    startProgressAnimation();
    
    try {
        // Build request body with advanced options
        const requestBody = { 
            repo_url: url,
            mode: selectedMode,
            persona: selectedPersona
        };
        if (deployUrl) {
            requestBody.deployed_link = deployUrl;
        }
        
        // Call the API
        const response = await fetch(`${API_BASE}/api/v1/grade`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to analyze repository');
        }
        
        const report = await response.json();
        currentReport = report;
        currentAssets = report.assets || [];
        
        // Complete progress
        completeProgress();
        
        // Wait a moment, then show results
        setTimeout(() => {
            hideSection('progressSection');
            showSection('resultsSection');
            renderReport(report);
        }, 500);
        
    } catch (error) {
        console.error('Analysis failed:', error);
        alert(`Analysis failed: ${error.message}`);
        resetToInput();
    }
}

function resetAndAnalyze() {
    document.getElementById('repoUrl').value = '';
    const deployInput = document.getElementById('deployUrl');
    if (deployInput) deployInput.value = '';
    resetToInput();
}

function resetToInput() {
    hideSection('progressSection');
    hideSection('resultsSection');
    showSection('inputSection');
    resetProgress();
    // Reset to overview tab
    switchTab('overview');
}

// ==========================================
// Progress Animation
// ==========================================

let progressInterval = null;
let currentStep = 0;

function updateProgressForMode(mode) {
    const title = document.querySelector('.progress-title');
    if (!title) return;
    
    if (mode === 'deep') {
        title.textContent = 'Deep Investigation in Progress...';
        // Update step descriptions for deep mode
        const stepTexts = [
            'Fetching complete repository data...',
            'Parsing notebooks, configs & infra files...',
            'Running security & code analysis...',
            'Generating detailed evaluation...'
        ];
        ['step1', 'step2', 'step3', 'step4'].forEach((id, i) => {
            const step = document.getElementById(id);
            if (step) {
                const span = step.querySelector('span');
                if (span) span.textContent = stepTexts[i];
            }
        });
    } else {
        title.textContent = 'Analyzing Repository';
        // Reset to default step descriptions
        const stepTexts = [
            'Fetching repository data...',
            'Scanning assets & files...',
            'Running AI evaluation...',
            'Verifying deployment...'
        ];
        ['step1', 'step2', 'step3', 'step4'].forEach((id, i) => {
            const step = document.getElementById(id);
            if (step) {
                const span = step.querySelector('span');
                if (span) span.textContent = stepTexts[i];
            }
        });
    }
}

function startProgressAnimation() {
    resetProgress();
    
    const steps = ['step1', 'step2', 'step3', 'step4'];
    const progressBar = document.getElementById('progressBar');
    let progress = 0;
    
    // Adjust speed based on mode
    const speedMultiplier = selectedMode === 'deep' ? 0.3 : 1;
    
    // Animate progress bar
    progressInterval = setInterval(() => {
        progress += Math.random() * 15 * speedMultiplier;
        if (progress > 90) progress = 90;
        progressBar.style.width = progress + '%';
        
        // Update steps
        const stepIndex = Math.floor(progress / 25);
        if (stepIndex !== currentStep && stepIndex < steps.length) {
            // Complete previous steps
            for (let i = 0; i < stepIndex; i++) {
                document.getElementById(steps[i]).classList.remove('active');
                document.getElementById(steps[i]).classList.add('completed');
            }
            // Activate current step
            if (stepIndex < steps.length) {
                document.getElementById(steps[stepIndex]).classList.add('active');
            }
            currentStep = stepIndex;
        }
    }, 300);
}

function completeProgress() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    
    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = '100%';
    
    // Complete all steps
    ['step1', 'step2', 'step3', 'step4'].forEach(id => {
        const step = document.getElementById(id);
        step.classList.remove('active');
        step.classList.add('completed');
    });
}

function resetProgress() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    
    currentStep = 0;
    document.getElementById('progressBar').style.width = '0%';
    
    ['step1', 'step2', 'step3', 'step4'].forEach(id => {
        const step = document.getElementById(id);
        step.classList.remove('active', 'completed');
    });
}

// ==========================================
// AI Engine Info Display
// ==========================================

function renderAIEngineInfo(report) {
    const container = document.getElementById('aiEngineInfo');
    if (!container) return;
    
    const mode = report.analysis_mode || 'fast';
    const persona = report.persona_used || 'Mentor';
    
    // Engine info based on mode
    const engineInfo = mode === 'deep' 
        ? { icon: '🧠', name: 'Gemini 1.5 Pro', desc: 'Deep Analysis' }
        : { icon: '🚀', name: 'Groq Llama-3', desc: 'Quick Scan' };
    
    container.innerHTML = `
        <div class="ai-engine-badge">
            <span class="engine-icon">${engineInfo.icon}</span>
            <span class="engine-name">${engineInfo.name}</span>
            <span class="engine-separator">•</span>
            <span class="engine-persona">${persona}</span>
        </div>
    `;
    container.style.display = 'flex';
}

// ==========================================
// Render Report
// ==========================================

function renderReport(report) {
    // Remove skeleton classes
    document.querySelectorAll('.skeleton').forEach(el => el.classList.remove('skeleton'));
    document.querySelectorAll('.skeleton-text').forEach(el => el.classList.remove('skeleton-text'));
    
    // Render score with animation
    animateScore(report.score);
    
    // Repo name and level
    document.getElementById('repoName').textContent = `${report.owner}/${report.repo_name}`;
    document.getElementById('levelText').textContent = report.level;
    document.getElementById('critique').textContent = `"${report.critique_tone}"`;
    
    // Show AI Engine used (Hybrid Engine indicator)
    renderAIEngineInfo(report);
    
    // THE 5 KEY AREAS - Metrics Grid
    // 1. Storefront (Documentation)
    renderMetric('Docs', report.metrics.docs_rating, 'Storefront', 'gradeDocs', 'barDocs');
    // 2. Skeleton (Structure)
    renderMetric('Structure', report.metrics.structure_rating, 'Skeleton', 'gradeStructure', 'barStructure');
    // 3. Work Ethic (Commits)
    const commitRating = report.metrics.commit_rating || estimateCommitRating(report.score);
    renderMetric('Commits', commitRating, 'WorkEthic', 'gradeCommits', 'barCommits');
    // 4. Quality Signals (Tests)
    renderMetric('Tests', report.metrics.test_rating, 'Quality', 'gradeTests', 'barTests');
    // 5. Real-World Value (calculated from overall employability)
    const valueRating = report.metrics.employability_score 
        ? scoreToGrade(report.metrics.employability_score)
        : estimateValueRating(report.score, report.metrics);
    renderMetric('Value', valueRating, 'Value', 'gradeValue', 'barValue');
    
    // Summary
    document.getElementById('summaryText').textContent = report.summary;
    
    // Resume bullets
    const resumeList = document.getElementById('resumeList');
    resumeList.innerHTML = report.resume_bullets.map(bullet => 
        `<li class="resume-item">${bullet}</li>`
    ).join('');
    
    // Interview question
    document.getElementById('interviewQuestion').textContent = report.interview_question;
    
    // Roadmap
    renderRoadmap(report.roadmap);
    
    // NEW: Render Recruiter Verdict (THE KILLER FEATURE)
    renderVerdict(report);
    
    // NEW: Render Red/Green Flags (The Kill Sheet)
    renderFlags(report);
    
    // Deployment status
    renderDeploymentStatus(report);
    
    // Update tab badges
    updateTabBadges(report);
    
    // Render Code Map
    renderCodeMap(report.file_diagram || []);
    
    // Render Assets Gallery
    renderAssets(report.assets || []);
}

// ==========================================
// NEW: Render Recruiter Verdict
// ==========================================
function renderVerdict(report) {
    const verdictCard = document.getElementById('verdictCard');
    const verdictBadge = document.getElementById('verdictBadge');
    const verdictText = document.getElementById('verdictText');
    const verdictReason = document.getElementById('verdictReason');
    
    if (!verdictCard) return;
    
    // Get verdict from report or generate from score
    let verdict = report.recruiter_verdict || generateVerdictFromScore(report.score);
    let verdictType = getVerdictType(verdict);
    
    // Extract reason if included (format: "Verdict: reason")
    let reason = '';
    if (verdict.includes(':')) {
        const parts = verdict.split(':');
        verdict = parts[0].trim();
        reason = parts.slice(1).join(':').trim();
    } else if (verdict.includes('.')) {
        const parts = verdict.split('.');
        verdict = parts[0].trim();
        reason = parts.slice(1).join('.').trim();
    }
    
    verdictBadge.className = `verdict-badge ${verdictType}`;
    verdictText.textContent = verdict;
    verdictReason.textContent = reason || getDefaultReason(report.score);
    verdictCard.classList.remove('skeleton');
}

function generateVerdictFromScore(score) {
    if (score >= 86) return 'Strong Hire';
    if (score >= 76) return 'Hire';
    if (score >= 66) return 'Lean Hire';
    if (score >= 51) return 'Lean No Hire';
    if (score >= 31) return 'No Hire';
    return 'Strong No Hire';
}

function getVerdictType(verdict) {
    const v = verdict.toLowerCase();
    if (v.includes('strong hire')) return 'strong-hire';
    if (v.includes('hire') && !v.includes('no')) return 'hire';
    if (v.includes('lean hire')) return 'lean-hire';
    if (v.includes('lean no')) return 'lean-no-hire';
    if (v.includes('strong no')) return 'strong-no-hire';
    if (v.includes('no hire')) return 'no-hire';
    return 'lean-hire'; // default
}

function getDefaultReason(score) {
    if (score >= 86) return 'Exceptional work that rivals professional projects. Would fast-track this candidate.';
    if (score >= 76) return 'Impressive for a student. Would recommend for technical interview.';
    if (score >= 66) return 'Competent work with most elements present. Would pass initial screen.';
    if (score >= 51) return 'Shows effort but lacks professional polish. Needs improvement before applying.';
    if (score >= 31) return 'Code exists but screams "tutorial follower." No personal touches visible.';
    return 'Would embarrass the candidate if shown to a recruiter. Needs complete overhaul.';
}

// ==========================================
// NEW: Render Red/Green Flags
// ==========================================
function renderFlags(report) {
    const redFlagsCard = document.getElementById('redFlagsCard');
    const greenFlagsCard = document.getElementById('greenFlagsCard');
    const redFlagsList = document.getElementById('redFlagsList');
    const greenFlagsList = document.getElementById('greenFlagsList');
    
    if (!redFlagsList || !greenFlagsList) return;
    
    // Get flags from report or generate from metrics
    const redFlags = report.red_flags && report.red_flags.length > 0 
        ? report.red_flags 
        : generateRedFlags(report);
    const greenFlags = report.green_flags && report.green_flags.length > 0 
        ? report.green_flags 
        : generateGreenFlags(report);
    
    redFlagsList.innerHTML = redFlags.length > 0
        ? redFlags.map(flag => `<li class="flag-item">${flag}</li>`).join('')
        : '<li class="flag-item" style="color: var(--success);">No major red flags detected!</li>';
    
    greenFlagsList.innerHTML = greenFlags.length > 0
        ? greenFlags.map(flag => `<li class="flag-item">${flag}</li>`).join('')
        : '<li class="flag-item" style="color: var(--text-muted);">Keep improving to earn green flags!</li>';
    
    redFlagsCard.classList.remove('skeleton');
    greenFlagsCard.classList.remove('skeleton');
}

function generateRedFlags(report) {
    const flags = [];
    if (report.metrics.test_rating === 'F') flags.push('Zero test coverage - major employability risk');
    if (report.metrics.docs_rating === 'F') flags.push('Missing README - recruiters will skip this instantly');
    if (report.metrics.structure_rating === 'F') flags.push('Chaotic folder structure - looks unprofessional');
    if (report.score < 40) flags.push('Overall quality below interview threshold');
    return flags;
}

function generateGreenFlags(report) {
    const flags = [];
    if (report.metrics.test_rating === 'A') flags.push('Comprehensive test suite - shows professional mindset');
    if (report.metrics.docs_rating === 'A') flags.push('Excellent documentation - easy to evaluate');
    if (report.metrics.structure_rating === 'A') flags.push('Clean architecture - demonstrates senior-level thinking');
    if (report.score >= 80) flags.push('Portfolio-ready project - would impress recruiters');
    if (report.deployment_status === 'live') flags.push('Live deployment - shows ability to ship');
    return flags;
}

function animateScore(targetScore) {
    const scoreNumber = document.getElementById('scoreNumber');
    const scoreRing = document.getElementById('scoreRing');
    
    // Animate number
    let current = 0;
    const duration = 1500;
    const startTime = Date.now();
    
    function updateNumber() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3); // Ease out cubic
        
        current = Math.floor(easeProgress * targetScore);
        scoreNumber.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        } else {
            scoreNumber.textContent = targetScore;
        }
    }
    
    updateNumber();
    
    // Animate ring
    const circumference = 565.48; // 2 * π * 90
    const offset = circumference - (targetScore / 100) * circumference;
    
    setTimeout(() => {
        scoreRing.style.strokeDashoffset = offset;
    }, 100);
}

function renderMetric(name, grade, displayName, gradeId, barId) {
    const gradeEl = document.getElementById(gradeId);
    const barEl = document.getElementById(barId);
    
    gradeEl.textContent = grade;
    gradeEl.className = 'metric-grade grade-' + grade.toLowerCase();
    
    const percentage = GRADE_PERCENTAGES[grade] || 50;
    barEl.className = 'metric-bar-fill grade-' + grade.toLowerCase();
    
    setTimeout(() => {
        barEl.style.width = percentage + '%';
    }, 300);
}

function renderRoadmap(roadmap) {
    const container = document.getElementById('roadmapList');
    
    container.innerHTML = roadmap.map((item, index) => `
        <div class="roadmap-item priority-${item.priority.toLowerCase()}">
            <div class="roadmap-number">${index + 1}</div>
            <div class="roadmap-content">
                <div class="roadmap-step">${item.step}</div>
                <div class="roadmap-description">${item.description}</div>
                ${item.impact ? `<div class="roadmap-impact">💡 ${item.impact}</div>` : ''}
            </div>
            <div class="priority-badge ${item.priority.toLowerCase()}">${item.priority}</div>
        </div>
    `).join('');
}

// ==========================================
// Utility Functions
// ==========================================

function showSection(id) {
    document.getElementById(id).classList.remove('hidden');
}

function hideSection(id) {
    document.getElementById(id).classList.add('hidden');
}

function isValidGitHubUrl(url) {
    const pattern = /^(https?:\/\/)?(www\.)?github\.com\/[\w-]+\/[\w.-]+\/?$/i;
    return pattern.test(url);
}

function shakeInput(input) {
    input.style.animation = 'shake 0.5s ease';
    setTimeout(() => {
        input.style.animation = '';
    }, 500);
}

// Add shake animation
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
`;
document.head.appendChild(style);

// Add SVG gradient definition
document.addEventListener('DOMContentLoaded', () => {
    const svg = document.querySelector('.score-ring');
    if (svg) {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        defs.innerHTML = `
            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#6366f1"/>
                <stop offset="50%" stop-color="#8b5cf6"/>
                <stop offset="100%" stop-color="#a855f7"/>
            </linearGradient>
        `;
        svg.insertBefore(defs, svg.firstChild);
    }
    
    // Enable Enter key to submit
    document.getElementById('repoUrl').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            analyzeRepo();
        }
    });
});

// ==========================================
// Tab Switching
// ==========================================

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// ==========================================
// Deployment Status
// ==========================================

function renderDeploymentStatus(report) {
    const liveDemoBtn = document.getElementById('liveDemoBtn');
    const deployBroken = document.getElementById('deployBroken');
    
    // Hide both by default
    liveDemoBtn.classList.add('hidden');
    deployBroken.classList.add('hidden');
    
    if (report.deployment_status === 'live' && report.deployed_link) {
        liveDemoBtn.href = report.deployed_link;
        liveDemoBtn.classList.remove('hidden');
    } else if (report.deployment_status === 'broken') {
        deployBroken.classList.remove('hidden');
    }
}

// ==========================================
// Tab Badges
// ==========================================

function updateTabBadges(report) {
    const fileCount = (report.file_diagram || []).length;
    const assetCount = (report.assets || []).length;
    
    document.getElementById('codeMapBadge').textContent = fileCount;
    document.getElementById('assetsBadge').textContent = assetCount;
}

// ==========================================
// Code Map Rendering
// ==========================================

function renderCodeMap(fileDiagram) {
    const container = document.getElementById('codeMapDiagram');
    
    if (!fileDiagram || fileDiagram.length === 0) {
        container.innerHTML = `
            <div class="codemap-placeholder">
                <span class="placeholder-icon">📂</span>
                <p>No file structure data available</p>
            </div>
        `;
        return;
    }
    
    // Sort: folders first, then files, then by health priority
    const healthPriority = { 'critical': 0, 'warning': 1, 'healthy': 2 };
    const sorted = [...fileDiagram].sort((a, b) => {
        if (a.type !== b.type) return a.type === 'folder' ? -1 : 1;
        return healthPriority[a.health] - healthPriority[b.health];
    });
    
    container.innerHTML = sorted.map(node => {
        const icon = getFileIcon(node);
        const issueCount = node.issues ? node.issues.length : 0;
        const issueText = issueCount > 0 ? `${issueCount} issue${issueCount > 1 ? 's' : ''}` : '';
        
        return `
            <div class="file-node ${node.health}" onclick="showFileDetails('${escapeHtml(node.path)}', '${node.health}', ${JSON.stringify(node.issues || []).replace(/"/g, '&quot;')})">
                <span class="file-node-icon">${icon}</span>
                <span class="file-node-name">${escapeHtml(node.name)}</span>
                ${issueText ? `<span class="file-node-issues">${issueText}</span>` : ''}
            </div>
        `;
    }).join('');
}

function getFileIcon(node) {
    if (node.type === 'folder') return FILE_ICONS.folder;
    
    const ext = node.name.split('.').pop().toLowerCase();
    return FILE_ICONS[ext] || FILE_ICONS.default;
}

function showFileDetails(path, health, issues) {
    const issueList = issues.length > 0 
        ? `\n\nIssues:\n${issues.map(i => `• ${i}`).join('\n')}`
        : '';
    
    const statusEmoji = health === 'healthy' ? '✅' : health === 'warning' ? '⚠️' : '❌';
    alert(`${statusEmoji} ${path}\n\nHealth: ${health.charAt(0).toUpperCase() + health.slice(1)}${issueList}`);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==========================================
// Assets Gallery Rendering
// ==========================================

function renderAssets(assets) {
    const gallery = document.getElementById('assetsGallery');
    const placeholder = document.getElementById('assetsPlaceholder');
    const downloadAllBtn = document.getElementById('downloadAllBtn');
    
    if (!assets || assets.length === 0) {
        placeholder.style.display = 'flex';
        downloadAllBtn.classList.add('hidden');
        return;
    }
    
    placeholder.style.display = 'none';
    downloadAllBtn.classList.remove('hidden');
    
    gallery.innerHTML = assets.map(asset => {
        const isImage = asset.type === 'image';
        const preview = isImage 
            ? `<img src="${asset.url}" alt="${escapeHtml(asset.name)}" loading="lazy" onerror="this.parentElement.innerHTML='<span class=\\'asset-preview-video\\'>🖼️</span>'">`
            : `<span class="asset-preview-video">🎬</span>`;
        
        return `
            <div class="asset-card">
                <div class="asset-preview">
                    ${preview}
                    <div class="asset-overlay">
                        <a href="${asset.url}" class="asset-download-btn" download="${asset.name}" target="_blank">
                            ⬇️ Download
                        </a>
                    </div>
                </div>
                <div class="asset-info">
                    <div class="asset-name">${escapeHtml(asset.name)}</div>
                    <div class="asset-path">${escapeHtml(asset.path)}</div>
                </div>
            </div>
        `;
    }).join('');
}

function downloadAllAssets() {
    if (!currentAssets || currentAssets.length === 0) {
        alert('No assets to download');
        return;
    }
    
    // Open each asset URL in a new tab for download
    // (Proper zip download would require JSZip library)
    currentAssets.forEach((asset, index) => {
        setTimeout(() => {
            const link = document.createElement('a');
            link.href = asset.url;
            link.download = asset.name;
            link.target = '_blank';
            link.click();
        }, index * 200);
    });
}
