# Search Settings Feature

## Overview
Users can now control how hashtag matching works when receiving messages and searching data.

## What Changed

### 1. Three Search Modes

#### **Match ANY hashtag** (Default)
- User receives messages containing **at least ONE** of their subscribed hashtags
- Example: If user subscribes to `#python` and `#django`
  - They receive messages with `#python` only
  - They receive messages with `#django` only
  - They receive messages with both `#python` and `#django`

#### **Match ALL hashtags**
- User receives messages containing **ALL** of their subscribed hashtags
- Example: If user subscribes to `#python` and `#django`
  - They ONLY receive messages that have BOTH `#python` AND `#django`
  - Messages with just `#python` or just `#django` are ignored

#### **Advanced (AND/OR Groups)** ⭐ NEW
- User can separate hashtags into **REQUIRED** (must all match) and **OPTIONAL** (any can match)
- Logic: **(ALL Required) AND (ANY Optional)**
- Example: Required: `#python` `#django`, Optional: `#backend` `#api`
  - Messages MUST have BOTH `#python` AND `#django`
  - AND MUST have at least one of `#backend` OR `#api`
  - This gives you: `(#python AND #django) AND (#backend OR #api)`

### 2. User Interface

#### New Button
- Added "Search Settings" button to the main keyboard
- Users can tap it to configure their preferences

#### Settings Screen
- Shows current mode with ✅ indicator
- Clear explanations of each mode
- Easy toggle between modes
- Instant feedback when settings are updated

#### Configure Hashtag Groups (Advanced Mode)
- Visual interface with color-coded indicators:
  - ⚪️ Not set - Hashtag not used in matching
  - 🔴 Required (AND) - MUST be present
  - 🟡 Optional (OR) - At least one must be present
- Tap any hashtag to cycle through states
- Real-time updates showing current configuration
- Shows the logic: (All Required) AND (Any Optional)

### 3. Where It Works

The match mode applies to:
1. **Real-time message forwarding** (`send_new_message()`)
   - When new messages arrive from Telegram channels
   
2. **Batch sending** (`send_data()`)
   - When running `python main.py send_data`
   
3. **Manual search** (Search button in bot)
   - When users click "Search" to find existing messages

### 4. Technical Implementation

#### Database Structure
Each user now has enhanced search configuration fields:
```json
{
  "id": 123456789,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "hashtags": ["#python", "#django", "#backend", "#api"],
  "match_mode": "advanced",  // "any", "all", or "advanced"
  "required_hashtags": ["#python", "#django"],  // For advanced mode
  "optional_hashtags": ["#backend", "#api"]     // For advanced mode
}
```

#### Code Changes

**main.py:**
- Updated `send_new_message()` to check `match_mode`
- Updated `send_data()` to use appropriate TinyDB query

**bot/my_bot.py:**
- Added `search_settings()` function
- Added `search_settings_button()` callback handler
- Added `configure_groups()` function for hashtag grouping interface
- Added `toggle_hashtag_group()` to cycle hashtags through states
- Updated `search()` to respect `match_mode` including advanced mode
- Added "Search Settings" keyboard button
- New callback handlers for `config_groups`, `done_groups`, and `toggle_*`

## How Users Use It

### Basic Mode Setup
1. Start the bot or send `/start`
2. Click "Search Settings" button
3. Choose between:
   - "Match ANY hashtag" (more results)
   - "Match ALL hashtags" (strict filtering)
   - "Advanced (AND/OR groups)" (custom logic)
4. Settings are saved automatically
5. All future messages and searches use the selected mode

### Advanced Mode Configuration
1. Click "Search Settings"
2. Select "Advanced (AND/OR groups)"
3. Click "⚙️ Configure Hashtag Groups"
4. For each hashtag, tap to cycle:
   - ⚪️ Not set → 🔴 Required → 🟡 Optional → ⚪️ Not set (cycles)
5. Click "✅ Done" when finished
6. Your custom logic is now active!

**Example Setup:**
- You have hashtags: `#python`, `#django`, `#backend`, `#frontend`
- Set `#python` and `#django` as 🔴 Required
- Set `#backend` and `#frontend` as 🟡 Optional
- Result: Get messages with `#python AND #django AND (#backend OR #frontend)`

## Benefits

✅ **Flexibility**: Users control their notification preferences
✅ **Better filtering**: Reduce noise with "Match ALL" mode
✅ **More discovery**: Find more content with "Match ANY" mode
✅ **Advanced logic**: Create complex matching rules with AND/OR groups
✅ **Visual interface**: Color-coded indicators make configuration intuitive
✅ **User-friendly**: Clear interface with examples
✅ **Persistent**: Settings saved permanently for each user
✅ **Precise targeting**: Get exactly the messages you want with advanced mode

## Default Behavior

- New users default to "Match ANY" mode
- Existing users without `match_mode` field default to "Match ANY"
- This maintains backward compatibility

## Testing

To test the feature:
1. Run the bot
2. Add multiple hashtags (e.g., `#python #django #backend #api`)
3. Try "Match ANY" mode and search
4. Switch to "Match ALL" mode and search again
5. Switch to "Advanced" mode:
   - Configure `#python` and `#django` as Required (🔴)
   - Configure `#backend` and `#api` as Optional (🟡)
   - Search and verify you only get messages matching the logic
6. Compare the results across different modes

## Real-World Use Cases

### Use Case 1: Job Seeker
- Required: `#python` `#remote` (must have both)
- Optional: `#senior` `#mid-level` (either seniority level)
- Gets: Remote Python jobs at senior or mid level

### Use Case 2: Learning Resources
- Required: `#tutorial` (must be a tutorial)
- Optional: `#python` `#javascript` `#golang` (any language)
- Gets: Tutorials in any of the specified languages

### Use Case 3: Tech News
- Required: `#AI` `#news` (must be AI news)
- Optional: `#openai` `#anthropic` `#google` (from any company)
- Gets: AI news from specific companies

## Future Enhancements

Possible improvements:
- Multiple AND groups with OR between them: `(A AND B) OR (C AND D)`
- Minimum match count (e.g., "at least 2 out of 3 hashtags")
- Percentage-based matching (e.g., "at least 50% match")
- Exclude/negative hashtags (e.g., "must NOT have #javascript")
- Weighted priorities (some hashtags more important than others)
