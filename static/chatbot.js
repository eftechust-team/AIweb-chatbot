// Chatbot JavaScript - handles food input, API calls, and UI updates

class NutritionChatbot {
    constructor() {
        this.dailyNutrition = {
            carbs: 0,
            protein: 0,
            fat: 0
        };
        this.userInfo = {};
        this.profiles = [];
        this.lastProfileId = null;
        this.conversationHistory = [];
        this.init();
    }

    init() {
        // DOM elements
        this.messagesContainer = document.getElementById('messages-container');
        this.foodInput = document.getElementById('food-input');
        this.foodInputForm = document.getElementById('food-input-form');
        this.userInfoForm = document.getElementById('user-info-form');
        this.analyzeBtn = document.getElementById('analyze-btn');
        this.undoBtn = document.getElementById('undo-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.profileSelect = document.getElementById('profile-select');
        this.saveProfileBtn = document.getElementById('save-profile-btn');
        this.renameProfileBtn = document.getElementById('rename-profile-btn');
        this.deleteProfileBtn = document.getElementById('delete-profile-btn');

        // Counters
        this.carbsDisplay = document.getElementById('carbs-total');
        this.proteinDisplay = document.getElementById('protein-total');
        this.fatDisplay = document.getElementById('fat-total');

        // Event listeners
        this.foodInputForm.addEventListener('submit', (e) => this.handleFoodInput(e));
        this.userInfoForm.addEventListener('change', () => this.updateUserInfo());
        this.analyzeBtn.addEventListener('click', () => this.handleAnalyze());
        this.undoBtn.addEventListener('click', () => this.undoLast());
        this.clearBtn.addEventListener('click', () => this.clearAll());
        this.profileSelect.addEventListener('change', () => this.handleProfileSelect());
        this.saveProfileBtn.addEventListener('click', () => this.handleSaveProfile());
        this.renameProfileBtn.addEventListener('click', () => this.handleRenameProfile());
        this.deleteProfileBtn.addEventListener('click', () => this.handleDeleteProfile());

        // Load saved data from localStorage
        this.loadSavedData();
        
        // Update button status based on loaded data
        this.updateAnalyzeButtonStatus();
    }

    loadSavedData() {
        const savedNutrition = localStorage.getItem('dailyNutrition');
        const savedUserInfo = localStorage.getItem('userInfo');
        const savedProfiles = localStorage.getItem('profiles');
        const savedLastProfileId = localStorage.getItem('lastProfileId');

        if (savedNutrition) {
            this.dailyNutrition = JSON.parse(savedNutrition);
            this.updateDisplay();
        }

        if (savedProfiles) {
            try {
                this.profiles = JSON.parse(savedProfiles);
            } catch (err) {
                console.error('Failed to parse profiles', err);
                this.profiles = [];
            }
        }

        if (savedLastProfileId) {
            this.lastProfileId = savedLastProfileId || null;
        }

        // If we have a last profile, load it; otherwise fall back to plain userInfo storage
        if (this.lastProfileId && this.getProfileById(this.lastProfileId)) {
            this.loadProfile(this.lastProfileId, { silent: true });
        } else if (savedUserInfo) {
            this.userInfo = JSON.parse(savedUserInfo);
            this.populateUserForm();
        }

        this.updateProfileSelect();
    }

    saveData() {
        localStorage.setItem('dailyNutrition', JSON.stringify(this.dailyNutrition));
        localStorage.setItem('userInfo', JSON.stringify(this.userInfo));
        localStorage.setItem('profiles', JSON.stringify(this.profiles));
        localStorage.setItem('lastProfileId', this.lastProfileId || '');
    }

    getProfileById(id) {
        return this.profiles.find(p => p.id === id);
    }

    updateProfileSelect() {
        if (!this.profileSelect) return;
        this.profileSelect.innerHTML = '<option value="">Select...</option>';
        this.profiles.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name;
            this.profileSelect.appendChild(opt);
        });

        if (this.lastProfileId) {
            this.profileSelect.value = this.lastProfileId;
        }
    }

    handleProfileSelect() {
        const profileId = this.profileSelect.value;
        if (!profileId) return;
        this.loadProfile(profileId);
    }

    handleSaveProfile() {
        // Ensure we have the latest form values
        this.updateUserInfo();

        const name = prompt('Save profile as:', 'My profile');
        if (!name) return;

        // Overwrite if a profile with the same name exists
        const existing = this.profiles.find(p => p.name.toLowerCase() === name.toLowerCase());
        if (existing) {
            existing.data = { ...this.userInfo };
            this.lastProfileId = existing.id;
        } else {
            const newProfile = {
                id: `profile-${Date.now()}`,
                name: name.trim(),
                data: { ...this.userInfo },
            };
            this.profiles.push(newProfile);
            this.lastProfileId = newProfile.id;
        }

        this.updateProfileSelect();
        this.saveData();
        this.addMessage(`💾 Saved profile "${name}".`, 'bot');
    }

    handleRenameProfile() {
        const profileId = this.profileSelect.value;
        if (!profileId) {
            this.addMessage('⚠️ Select a profile to rename.', 'bot');
            return;
        }

        const profile = this.getProfileById(profileId);
        if (!profile) return;

        const newName = prompt('Rename profile to:', profile.name);
        if (!newName) return;

        profile.name = newName.trim();
        this.updateProfileSelect();
        this.saveData();
        this.addMessage(`✏️ Renamed profile to "${newName}".`, 'bot');
    }

    handleDeleteProfile() {
        const profileId = this.profileSelect.value;
        if (!profileId) {
            this.addMessage('⚠️ Select a profile to delete.', 'bot');
            return;
        }

        const profile = this.getProfileById(profileId);
        if (!profile) return;

        const ok = confirm(`Delete profile "${profile.name}"?`);
        if (!ok) return;

        this.profiles = this.profiles.filter(p => p.id !== profileId);
        if (this.lastProfileId === profileId) {
            this.lastProfileId = null;
        }
        this.profileSelect.value = '';
        this.updateProfileSelect();
        this.saveData();
        this.addMessage(`🗑️ Deleted profile "${profile.name}".`, 'bot');
    }

    loadProfile(profileId, { silent = false } = {}) {
        const profile = this.getProfileById(profileId);
        if (!profile) return;
        this.userInfo = { ...profile.data };
        this.populateUserForm();
        this.lastProfileId = profileId;
        this.saveData();
        this.updateAnalyzeButtonStatus();
        if (!silent) {
            this.addMessage(`📥 Loaded profile "${profile.name}".`, 'bot');
        }
    }

    updateUserInfo() {
        const formData = new FormData(this.userInfoForm);
        this.userInfo = {
            gender: formData.get('gender'),
            age: formData.get('age'),
            height: formData.get('height'),
            weight: formData.get('weight'),
            activity: formData.get('activity'),
            diet: formData.get('diet'),
            preference: formData.get('preference')
        };
        this.saveData();
        this.updateAnalyzeButtonStatus();
    }

    populateUserForm() {
        if (this.userInfo.gender) {
            document.querySelector(`input[name="gender"][value="${this.userInfo.gender}"]`).checked = true;
        }
        if (this.userInfo.age) document.querySelector('input[name="age"]').value = this.userInfo.age;
        if (this.userInfo.height) document.querySelector('input[name="height"]').value = this.userInfo.height;
        if (this.userInfo.weight) document.querySelector('input[name="weight"]').value = this.userInfo.weight;
        if (this.userInfo.activity) document.querySelector('select[name="activity"]').value = this.userInfo.activity;
        if (this.userInfo.diet) document.querySelector('select[name="diet"]').value = this.userInfo.diet;
        if (this.userInfo.preference) {
            document.querySelector(`input[name="preference"][value="${this.userInfo.preference}"]`).checked = true;
        }
    }

    async handleFoodInput(e) {
        e.preventDefault();

        const foodInput = this.foodInput.value.trim();
        if (!foodInput) return;

        // Add user message to chat
        this.addMessage(foodInput, 'user');
        this.foodInput.value = '';

        // Check for direct macro input (e.g., "50g carbs", "+30g protein", "-20g fat")
        const directMacroMatch = foodInput.match(/^([+-]?\d+(?:\.\d+)?)\s*g?\s*(carb|carbon|carbohydrate|protein|fat)s?$/i);
        if (directMacroMatch) {
            const amount = parseFloat(directMacroMatch[1]);
            const macroType = directMacroMatch[2].toLowerCase();
            
            let macroName = '';
            let nutrition = { carbs: 0, protein: 0, fat: 0 };
            
            if (macroType === 'carb' || macroType === 'carbon' || macroType === 'carbohydrate') {
                nutrition.carbs = amount;
                macroName = 'Carbohydrates';
            } else if (macroType === 'protein') {
                nutrition.protein = amount;
                macroName = 'Protein';
            } else if (macroType === 'fat') {
                nutrition.fat = amount;
                macroName = 'Fat';
            }
            
            this.addFoodToDaily(nutrition);
            
            const actionText = amount >= 0 ? 'added' : 'removed';
            const responseMsg = `✅ <strong>${macroName}</strong>
            
<div class="food-item-display">
    <div class="food-name">${Math.abs(amount)}g ${actionText} directly</div>
    <div class="nutrition-row">
        <span>Carbs:</span>
        <span>${nutrition.carbs}g</span>
    </div>
    <div class="nutrition-row">
        <span>Protein:</span>
        <span>${nutrition.protein}g</span>
    </div>
    <div class="nutrition-row">
        <span>Fat:</span>
        <span>${nutrition.fat}g</span>
    </div>
</div>

Your daily totals have been updated. Keep tracking!`;
            
            this.addMessage(responseMsg, 'bot');
            
            // Add to conversation history
            this.conversationHistory.push({
                input: foodInput,
                nutrition: { ...nutrition, food_name: macroName, quantity: amount, unit: 'g' },
                timestamp: new Date()
            });
            
            this.updateAnalyzeButtonStatus();
            this.saveData();
            return;
        }

        // Show loading state
        const loadingMsg = this.addMessage('🔍 Searching USDA database...', 'bot', true);

        try {
            // Call the API
            const response = await fetch('/api/search-food', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ food_input: foodInput })
            });

            const result = await response.json();

            if (!response.ok) {
                // More helpful error messages
                let errorMsg = result.error || 'Unable to find food information';
                if (errorMsg.includes('No foods found')) {
                    errorMsg += '\n\nTry being more specific (e.g., "chicken breast" instead of just "chicken")';
                }
                this.updateMessage(loadingMsg, `❌ ${errorMsg}`);
                return;
            }

            // Extract nutrition data
            const nutrition = result.nutrition;
            
            // Check if nutrition data is actually valid (not all zeros)
            if (nutrition.carbs === 0 && nutrition.protein === 0 && nutrition.fat === 0) {
                this.updateMessage(loadingMsg, `⚠️ Found "${nutrition.food_name}" but nutrition data appears incomplete.\n\nThis might be a data limitation with the USDA database for this item. Try a different food or variation.`);
                return;
            }
            
            this.addFoodToDaily(nutrition);

            // Generate friendly response
            const responseMsg = this.generateFoodResponse(nutrition);
            this.updateMessage(loadingMsg, responseMsg);

            // Add to conversation history
            this.conversationHistory.push({
                input: foodInput,
                nutrition: nutrition,
                timestamp: new Date()
            });

            // Auto-update analyze button status
            this.updateAnalyzeButtonStatus();
            
            this.saveData();

        } catch (error) {
            console.error('Error:', error);
            this.updateMessage(loadingMsg, '❌ Error processing food. Please try again.');
        }
    }

    generateFoodResponse(nutrition) {
        return `
✅ <strong>${nutrition.food_name}</strong>

<div class="food-item-display">
    <div class="food-name">${nutrition.quantity}${nutrition.unit} added</div>
    <div class="nutrition-row">
        <span>Carbs:</span>
        <span>${nutrition.carbs}g</span>
    </div>
    <div class="nutrition-row">
        <span>Protein:</span>
        <span>${nutrition.protein}g</span>
    </div>
    <div class="nutrition-row">
        <span>Fat:</span>
        <span>${nutrition.fat}g</span>
    </div>
</div>

Your daily totals have been updated. Keep tracking!
        `;
    }

    addFoodToDaily(nutrition) {
        this.dailyNutrition.carbs += nutrition.carbs;
        this.dailyNutrition.protein += nutrition.protein;
        this.dailyNutrition.fat += nutrition.fat;

        // Round to 2 decimal places
        this.dailyNutrition.carbs = Math.round(this.dailyNutrition.carbs * 100) / 100;
        this.dailyNutrition.protein = Math.round(this.dailyNutrition.protein * 100) / 100;
        this.dailyNutrition.fat = Math.round(this.dailyNutrition.fat * 100) / 100;

        this.updateDisplay();
        this.saveData();
    }

    updateDisplay() {
        this.carbsDisplay.textContent = this.dailyNutrition.carbs.toFixed(1);
        this.proteinDisplay.textContent = this.dailyNutrition.protein.toFixed(1);
        this.fatDisplay.textContent = this.dailyNutrition.fat.toFixed(1);
    }

    addMessage(text, sender = 'bot', isLoading = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        if (isLoading) messageDiv.classList.add('loading');

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isLoading) {
            contentDiv.innerHTML = `<div class="loading-spinner"></div> ${text}`;
        } else {
            contentDiv.innerHTML = text;
        }

        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

        return messageDiv;
    }

    updateMessage(messageElement, newText) {
        const contentDiv = messageElement.querySelector('.message-content');
        contentDiv.innerHTML = newText;
        messageElement.classList.remove('loading');
    }

    async handleAnalyze() {
        // Validate user info - provide specific guidance
        const missingFields = [];
        
        if (!this.userInfo.gender) missingFields.push('Gender');
        if (!this.userInfo.age) missingFields.push('Age');
        if (!this.userInfo.height) missingFields.push('Height');
        if (!this.userInfo.weight) missingFields.push('Weight');
        if (!this.userInfo.activity || this.userInfo.activity === '') missingFields.push('Activity Level');
        if (!this.userInfo.diet || this.userInfo.diet === '') missingFields.push('Diet Plan');
        if (!this.userInfo.preference || this.userInfo.preference === '') missingFields.push('Food Preference');

        if (missingFields.length > 0) {
            this.addMessage(`📋 Missing information needed:\n• ${missingFields.join('\n• ')}\n\nPlease fill in the form on the left, then try again.`, 'bot');
            return;
        }

        // Check if at least some food has been logged
        if (this.dailyNutrition.carbs === 0 && this.dailyNutrition.protein === 0 && this.dailyNutrition.fat === 0) {
            this.addMessage('🍽️ No food logged yet. Please add some food items first, then I can give you recommendations!', 'bot');
            return;
        }

        const loadingMsg = this.addMessage('📊 Analyzing your nutrition and generating personalized recommendations...', 'bot', true);

        try {
            const response = await fetch('/api/calculate-recommendation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_info: this.userInfo,
                    daily_nutrition: this.dailyNutrition
                })
            });

            let result;
            if (response.headers.get('content-type')?.includes('application/json')) {
                result = await response.json();
            } else {
                const text = await response.text();
                if (!response.ok) {
                    this.updateMessage(loadingMsg, `❌ Error (${response.status}): ${text?.slice(0, 300) || 'Unable to generate recommendation'}`);
                    return;
                }
                // Fallback wrapper if server returned plain text success
                result = { recommendation: null, raw: text };
            }

            if (!response.ok) {
                this.updateMessage(loadingMsg, `❌ Error: ${result?.error || 'Unable to generate recommendation'}`);
                return;
            }

            const rec = result.recommendation;
            const responseMsg = this.generateRecommendationResponse(rec);
            this.updateMessage(loadingMsg, responseMsg);

            // Store recommendation for further use
            sessionStorage.setItem('lastRecommendation', JSON.stringify(rec));

        } catch (error) {
            console.error('Error:', error);
            this.updateMessage(loadingMsg, '❌ Error generating recommendation. Please try again.');
        }
    }

    updateAnalyzeButtonStatus() {
        // Enable/disable button based on current state
        const hasUserInfo = this.userInfo.gender && this.userInfo.age && this.userInfo.height && this.userInfo.weight;
        const hasFoodLogged = this.dailyNutrition.carbs > 0 || this.dailyNutrition.protein > 0 || this.dailyNutrition.fat > 0;
        
        if (hasUserInfo && hasFoodLogged) {
            this.analyzeBtn.style.opacity = '1';
            this.analyzeBtn.style.cursor = 'pointer';
            this.analyzeBtn.title = 'Ready! Click to get recommendations';
        } else {
            this.analyzeBtn.style.opacity = '0.7';
            this.analyzeBtn.style.cursor = 'not-allowed';
            
            if (!hasUserInfo) {
                this.analyzeBtn.title = 'Please fill in your personal info first';
            } else {
                this.analyzeBtn.title = 'Please add at least one food item first';
            }
        }
    }

    generateRecommendationResponse(rec) {
        // Generate multiple recommendation solutions
        let allSolutionsHTML = '';
        
        if (rec.results.length > 0) {
            rec.results.forEach((result, index) => {
                const [foods, carbSup, proteinSup, fatSup] = result;
                
                let foodList = '';
                if (foods.length > 0) {
                    foodList = foods.map(f => {
                        const meshLink = f.mesh 
                            ? `<br><a href="/download-stl/${f.mesh}" download class="btn-download" style="margin-left: 0px; margin-top: 4px; display: inline-block;">📥 Download STL</a>`
                            : '';
                        const dimensions = f.x && f.y && f.z 
                            ? `<span style="font-size: 11px; color: var(--muted); margin-left: 8px;">(${f.x}mm × ${f.y}mm × ${f.z}mm)</span>`
                            : '';
                        return `<li>${f.name}: ${f.gram}g ${dimensions}${meshLink}</li>`;
                    }).join('');
                } else {
                    foodList = '<li>No specific recommendations at this time</li>';
                }

                // Supplement totals for this solution
                const supplementInfo = `
<div style="margin-top: 8px; padding: 8px; background: rgba(255, 122, 61, 0.05); border-radius: 6px; font-size: 12px;">
    <strong>Supplement Totals:</strong> Carbs: ${carbSup}g | Protein: ${proteinSup}g | Fat: ${fatSup}g
</div>`;

                allSolutionsHTML += `
<div style="margin: 12px 0; padding: 12px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px;">
    <div style="font-weight: 600; margin-bottom: 8px; color: var(--accent);">Solution ${index + 1}</div>
    <ul style="margin: 4px 0; padding-left: 20px; font-size: 13px;">
        ${foodList}
    </ul>
    ${supplementInfo}
</div>`;
            });
        } else {
            allSolutionsHTML = '<div style="padding: 12px; background: var(--bg-secondary); border-radius: 8px;">No specific food recommendations at this time</div>';
        }

        return `
📊 <strong>Your Nutrition Recommendation</strong>

<div style="margin: 12px 0; padding: 12px; background: var(--bg-secondary); border-radius: 8px;">
    <div style="font-weight: 600; margin-bottom: 8px;">Daily Calorie Target: ${rec.calories} kcal</div>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <thead>
            <tr style="border-bottom: 2px solid var(--border);">
                <th style="padding: 8px; text-align: left;">Nutrient</th>
                <th style="padding: 8px; text-align: right;">Target</th>
                <th style="padding: 8px; text-align: right;">Have</th>
                <th style="padding: 8px; text-align: right;">Need</th>
            </tr>
        </thead>
        <tbody>
            <tr style="border-bottom: 1px solid var(--border);">
                <td style="padding: 8px;">Carbs</td>
                <td style="padding: 8px; text-align: right; font-weight: 600;">${rec.carbohydrate_intake}g</td>
                <td style="padding: 8px; text-align: right;">${this.dailyNutrition.carbs}g</td>
                <td style="padding: 8px; text-align: right; color: ${rec.carbohydrate_needed < 0 ? '#22c55e' : 'var(--accent)'};">${rec.carbohydrate_needed}g</td>
            </tr>
            <tr style="border-bottom: 1px solid var(--border);">
                <td style="padding: 8px;">Protein</td>
                <td style="padding: 8px; text-align: right; font-weight: 600;">${rec.protein_intake}g</td>
                <td style="padding: 8px; text-align: right;">${this.dailyNutrition.protein}g</td>
                <td style="padding: 8px; text-align: right; color: ${rec.protein_needed < 0 ? '#22c55e' : 'var(--accent)'};">${rec.protein_needed}g</td>
            </tr>
            <tr>
                <td style="padding: 8px;">Fat</td>
                <td style="padding: 8px; text-align: right; font-weight: 600;">${rec.fat_intake}g</td>
                <td style="padding: 8px; text-align: right;">${this.dailyNutrition.fat}g</td>
                <td style="padding: 8px; text-align: right; color: ${rec.fat_needed < 0 ? '#22c55e' : 'var(--accent)'};">${rec.fat_needed}g</td>
            </tr>
        </tbody>
    </table>
</div>

<strong>Suggested Food Combinations:</strong>
${allSolutionsHTML}

Keep tracking your meals to reach your targets! 🎯
        `;
    }

    undoLast() {
        if (this.conversationHistory.length === 0) {
            this.addMessage('⚠️ Nothing to undo. No food entries found.', 'bot');
            return;
        }

        // Get the last entry
        const lastEntry = this.conversationHistory.pop();
        const lastNutrition = lastEntry.nutrition;

        // Subtract from daily totals
        this.dailyNutrition.carbs -= lastNutrition.carbs;
        this.dailyNutrition.protein -= lastNutrition.protein;
        this.dailyNutrition.fat -= lastNutrition.fat;

        // Ensure no negative values
        this.dailyNutrition.carbs = Math.max(0, this.dailyNutrition.carbs);
        this.dailyNutrition.protein = Math.max(0, this.dailyNutrition.protein);
        this.dailyNutrition.fat = Math.max(0, this.dailyNutrition.fat);

        // Round to 2 decimal places
        this.dailyNutrition.carbs = Math.round(this.dailyNutrition.carbs * 100) / 100;
        this.dailyNutrition.protein = Math.round(this.dailyNutrition.protein * 100) / 100;
        this.dailyNutrition.fat = Math.round(this.dailyNutrition.fat * 100) / 100;

        this.updateDisplay();
        this.saveData();
        this.updateAnalyzeButtonStatus();

        this.addMessage(`↶ Undone: <strong>${lastNutrition.food_name}</strong> (${lastNutrition.quantity}${lastNutrition.unit}) has been removed from your daily totals.`, 'bot');
    }

    clearAll() {
        if (this.dailyNutrition.carbs === 0 && this.dailyNutrition.protein === 0 && this.dailyNutrition.fat === 0) {
            this.addMessage('⚠️ Nothing to clear. No food entries found.', 'bot');
            return;
        }

        // Confirm before clearing
        const confirmed = confirm('Are you sure you want to clear all food entries? This cannot be undone.');
        if (!confirmed) return;

        this.dailyNutrition = { carbs: 0, protein: 0, fat: 0 };
        this.conversationHistory = [];
        this.updateDisplay();
        this.saveData();
        this.updateAnalyzeButtonStatus();
        this.addMessage('✨ All food entries have been cleared. Your daily tracker has been reset!', 'bot');
    }

    resetDaily() {
        this.dailyNutrition = { carbs: 0, protein: 0, fat: 0 };
        this.conversationHistory = [];
        this.updateDisplay();
        this.saveData();
        this.addMessage('✨ Daily tracker has been reset. Start tracking your meals!', 'bot');
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new NutritionChatbot();
});
