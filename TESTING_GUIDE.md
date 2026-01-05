# ELEVATEFOODS Chatbot - Testing Guide

## Quick Test Checklist

Use this guide to test all chatbot features before deployment.

---

## 1. UI & Navigation Tests

### [ ] Basic Page Load
- [ ] Navigate to http://localhost:8080/chatbot
- [ ] Page loads without errors
- [ ] Header displays "ELEVATEFOODS" logo and step indicators
- [ ] Sidebar visible on the right with nutrition summary
- [ ] Chat area visible with initial bot message

### [ ] Responsive Design
- [ ] **Desktop (1200px+)**: Sidebar on left, chat on right
- [ ] **Tablet (768-1024px)**: Sidebar items rearranged, readable
- [ ] **Mobile (< 768px)**: Single column layout, touch-friendly buttons

### [ ] Form Elements
- [ ] Gender radio buttons selectable
- [ ] Age, Height, Weight inputs accept numbers
- [ ] Activity level dropdown works
- [ ] Diet plan dropdown works
- [ ] Food preference radio buttons selectable

---

## 2. Nutrition Tracking Tests

### [ ] Daily Totals Update
- [ ] Initial totals show 0.0g for all macros
- [ ] After entering food, totals increase
- [ ] Values are correct (from USDA data)
- [ ] Totals persist after page refresh

### [ ] Data Persistence
- [ ] Fill out user info, refresh page → data still there
- [ ] Add foods, refresh page → nutrition totals still there
- [ ] Clear localStorage → reset all data
- [ ] Use different browser → fresh start

---

## 3. Food Search & API Tests

### Test Food Inputs

#### Simple Weight-Based Inputs
```
Input: "100g chicken breast"
Expected: Found chicken, shows ~31g protein, ~0g carbs, ~3.6g fat

Input: "200g salmon"
Expected: Found salmon, shows protein/fat values

Input: "50g rice"
Expected: Found rice, shows ~37g carbs

Input: "1 medium apple"
Expected: Found apple, shows ~21g carbs
```

#### Volume-Based Inputs
```
Input: "1 cup milk"
Expected: ~240g equivalent, shows ~12g carbs, ~8g protein

Input: "2 cups rice"
Expected: ~480g equivalent, shows nutrition values

Input: "1 oz almonds"
Expected: ~28g equivalent
```

#### Natural Language Variations
```
"chicken breast 100g" → Should work
"100 grams chicken" → May not work (not in order)
"1 medium banana" → Should work
"1 banana" → May use default portion size
```

### [ ] Error Handling
- [ ] Empty input → Shows error message
- [ ] Non-existent food (e.g., "xyzfood") → "No foods found" message
- [ ] Network error → Graceful error display

### [ ] Loading States
- [ ] Loading spinner shows while API processes
- [ ] Message shows "Processing..."
- [ ] Spinner disappears when complete
- [ ] Can't send multiple requests simultaneously (optional)

---

## 4. Recommendation System Tests

### [ ] User Info Validation
- [ ] Missing gender → Error message when clicking button
- [ ] Missing height/weight → Error message
- [ ] Missing activity level → Error message
- [ ] Missing diet plan → Error message
- [ ] All filled → Generates recommendation

### [ ] Recommendation Calculation
After filling info and logging some food:

```
Example:
User: 30 yr old, 180cm, 75kg, male, moderately active
Logged: 100g chicken + 1 apple
Expected: 
  - Daily calorie target calculated (~2500 kcal approx)
  - Carbs target ~300g (logged 21g, need 279g)
  - Protein target ~156g (logged 31g, need 125g)
  - Fat target ~83g (logged 3.8g, need 79g)
  - Suggests foods to meet targets
```

### [ ] Recommendation Display
- [ ] Shows calorie target
- [ ] Shows carbs/protein/fat targets
- [ ] Shows current intake vs. needed
- [ ] Suggests specific foods (from existing system)
- [ ] Provides actionable recommendations

---

## 5. Chat Interaction Tests

### [ ] Message Display
- [ ] User messages appear on right (orange)
- [ ] Bot messages appear on left (light background)
- [ ] Messages have smooth enter animations
- [ ] Chat scrolls to newest message automatically
- [ ] Old messages are visible in scroll history

### [ ] Input Behavior
- [ ] Can type in input field
- [ ] "Send" button is clickable
- [ ] Enter key sends message (submit form)
- [ ] Input clears after sending
- [ ] Focus returns to input after sending

### [ ] Conversation Flow
```
1. Bot: "Hello! Tell me what you ate..."
2. User: "100g chicken breast"
3. Bot: Shows nutrition for chicken
4. User: "1 apple"
5. Bot: Shows nutrition, daily totals updated
6. User: [Fill user info]
7. User: [Click Get Recommendations]
8. Bot: Shows personalized nutrition plan
```

---

## 6. Data Accuracy Tests

### Known USDA Foods (Test Set)

| Food | Quantity | Expected Carbs | Expected Protein | Expected Fat |
|------|----------|-----------------|------------------|--------------|
| Chicken breast | 100g | ~0g | ~31g | ~3.6g |
| Apple | 1 medium (182g) | ~25g | ~0.3g | ~0.2g |
| Rice | 100g cooked | ~28g | ~2.7g | ~0.3g |
| Banana | 1 medium (118g) | ~27g | ~1.1g | ~0.3g |
| Egg | 1 large (50g) | ~0.6g | ~6.3g | ~5.3g |
| Broccoli | 100g | ~7g | ~2.8g | ~0.4g |
| Salmon | 100g | ~0g | ~25g | ~13g |

Run each test:
```
Input: "[qty] [food]"
Check: Values match table approximately (within 5%)
```

---

## 7. Browser Compatibility Tests

Test in different browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Mobile Safari (iPhone)
- [ ] Chrome Mobile (Android)

Check for:
- [ ] No console errors (F12)
- [ ] Buttons clickable
- [ ] Animations smooth
- [ ] Text readable
- [ ] Colors displaying correctly

---

## 8. Edge Cases & Error Handling

### [ ] Invalid Inputs
```
"" (empty) → Error: "No food input"
"   " (spaces) → Error or ignored
"123456789" (just number) → Parse error or "No food found"
"abc@#$%^" (special chars) → May search or error
```

### [ ] Extreme Values
```
"1000000g chicken" → May not parse correctly
"0.001g rice" → Very small portion
"999 cups milk" → Very large portion
```

### [ ] Rapid Requests
```
Send 10 messages quickly → System should handle gracefully
Network slow → Loading indicator visible
API timeout → Error message shown
```

### [ ] Storage Limits
```
Add 50+ foods → Should not break storage
Exceed localStorage limit → Graceful degradation
```

---

## 9. Performance Tests

### [ ] Load Time
- [ ] Initial page load < 2 seconds
- [ ] API response < 3 seconds
- [ ] Recommendation calculation < 2 seconds

### [ ] Resource Usage
- [ ] No memory leaks (check DevTools)
- [ ] No console errors or warnings
- [ ] Smooth scrolling in chat
- [ ] Animations not laggy

### [ ] Network
- [ ] API calls complete successfully
- [ ] Proper error handling if API down
- [ ] Handles offline mode gracefully

---

## 10. Manual Testing Scenarios

### Scenario 1: First Time User
```
1. Load chatbot
2. See "Tell me what you ate" message
3. Type "100g chicken breast"
4. See nutrition breakdown
5. Type "1 apple"
6. See totals updated
7. Fill in user info (sidebar)
8. Click "Get Recommendations"
9. See personalized plan
✅ Result: Should work smoothly
```

### Scenario 2: Returning User (with localStorage)
```
1. Close browser completely
2. Reopen localhost:8080/chatbot
3. User info still there
4. Daily totals still there
5. Chat history still there
✅ Result: Data persisted correctly
```

### Scenario 3: Mobile User
```
1. Open on mobile phone
2. Layout stacks vertically
3. Can scroll sidebar and chat
4. Input field is large enough to touch
5. Buttons are easy to click
6. Text is readable
7. No horizontal scrolling
✅ Result: Mobile UX is good
```

### Scenario 4: API Error
```
1. Temporarily disable internet
2. Enter food "chicken"
3. See error message
4. Turn internet back on
5. Try again - works
✅ Result: Graceful error handling
```

---

## Test Data for Bulk Testing

Use this food list for comprehensive testing:

```
Proteins:
- 100g chicken breast
- 150g lean beef
- 100g salmon fillet
- 2 eggs
- 100g tofu

Carbs:
- 1 medium apple
- 1 banana
- 1 cup rice
- 100g bread
- 1 potato

Fats:
- 1 oz almonds
- 1/2 avocado
- 1 tbsp olive oil
- 1 oz cheese
- 10 walnuts

Vegetables:
- 1 cup broccoli
- 1 cup spinach
- 1 carrot
- 1 tomato
- 1 cup lettuce
```

---

## Automated Test Cases (Optional)

If implementing automated testing:

```javascript
// Example test
test('should add food and update totals', async () => {
    chatbot.addFood({ carbs: 100, protein: 20, fat: 5 });
    expect(document.getElementById('carbs-total').textContent).toBe('100.0');
    expect(chatbot.dailyNutrition.carbs).toBe(100);
});

test('should parse food input correctly', () => {
    const [name, qty, unit] = chatbot.parseFoodInput('100g chicken');
    expect(name).toBe('chicken');
    expect(qty).toBe(100);
    expect(unit).toBe('g');
});

test('should fetch from USDA API', async () => {
    const result = await fetch('/api/search-food', {...});
    expect(result.status).toBe(200);
    expect(result.nutrition).toHaveProperty('carbs');
});
```

---

## Test Results Log

Track test results:

```
Date: ____/____ 
Tester: ___________
Browser: _________ Version: _____

Food Tracking: [ ] PASS [ ] FAIL
Recommendations: [ ] PASS [ ] FAIL
Data Persistence: [ ] PASS [ ] FAIL
Mobile Responsive: [ ] PASS [ ] FAIL
API Integration: [ ] PASS [ ] FAIL
Error Handling: [ ] PASS [ ] FAIL

Notes: ________________
Issues: _______________
```

---

## Known Test Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "No foods found" | DEMO_KEY limit | Get personal API key |
| Slow API response | High traffic | Retry or wait |
| Data not persisting | localStorage disabled | Enable in browser |
| Form not submitting | JavaScript disabled | Enable in browser |
| UI not responsive | Browser zoom | Reset to 100% zoom |

---

## Sign-Off

When all tests pass:

- [ ] UI/UX working correctly
- [ ] Food tracking functional
- [ ] API integration successful
- [ ] Recommendations accurate
- [ ] Data persists correctly
- [ ] Mobile responsive
- [ ] Error handling works
- [ ] Performance acceptable

**Ready for Production:** _____ (Date)

**Tested by:** _____________ (Name)

**Notes:** ________________________

---

## Support

If issues found during testing:
1. Check browser console (F12)
2. Review error messages
3. Test with USDA API key
4. Check internet connection
5. Refer to CHATBOT_GUIDE.md for more info
