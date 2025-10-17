# Advanced Hashtag Matching - Quick Guide

## The Problem You Wanted to Solve
You wanted a way to say: "I want messages with **hashtag1 AND hashtag2**, OR if it has **hashtag3**"

For example: `(#python AND #django) OR #fullstack`

## The Solution: Advanced Mode

### How It Works
In Advanced mode, you separate hashtags into two groups:

1. **🔴 Required (AND)** - ALL of these MUST be present
2. **🟡 Optional (OR)** - AT LEAST ONE of these must be present

**Logic:** `(ALL Required) AND (ANY Optional)`

## Example Scenarios

### Scenario 1: Job Search
**Want:** Python Django jobs that are either remote or in NYC

**Setup:**
- 🔴 Required: `#python` `#django`
- 🟡 Optional: `#remote` `#nyc`

**Result:** Get messages with:
- ✅ `#python #django #remote`
- ✅ `#python #django #nyc`
- ✅ `#python #django #remote #nyc`
- ❌ `#python #remote` (missing #django)
- ❌ `#django #nyc` (missing #python)

### Scenario 2: Tech Content
**Want:** Backend tutorials in any language

**Setup:**
- 🔴 Required: `#backend` `#tutorial`
- 🟡 Optional: `#python` `#nodejs` `#golang` `#java`

**Result:** Get messages with:
- ✅ `#backend #tutorial #python`
- ✅ `#backend #tutorial #nodejs #golang`
- ❌ `#backend #python` (missing #tutorial)
- ❌ `#tutorial #python` (missing #backend)

### Scenario 3: Your Original Request
**Want:** Messages with `(#hashtag1 AND #hashtag2) OR #hashtag3`

**Setup:**
- 🔴 Required: `#hashtag1` `#hashtag2`
- 🟡 Optional: `#hashtag3`

**Result:** Get messages with:
- ✅ `#hashtag1 #hashtag2` (has required + optional not needed if required present)
- ✅ `#hashtag1 #hashtag2 #hashtag3` (has everything)

**Note:** If you want pure OR logic `#hashtag1 AND #hashtag2` OR just `#hashtag3`, you would need to use "Match ANY" mode with just those hashtags, or set up two separate subscriptions.

## How to Configure

```
1. Open bot → "Search Settings"
2. Select "Advanced (AND/OR groups)"
3. Tap "⚙️ Configure Hashtag Groups"
4. Tap each hashtag to cycle:
   ⚪️ → 🔴 → 🟡 → ⚪️
5. Click "✅ Done"
```

## Visual Flow

```
Your Hashtags: #python #django #remote #onsite

Configuration:
┌─────────────────────┐
│ 🔴 #python          │ ← Tap to Required
│ 🔴 #django          │ ← Tap to Required
│ 🟡 #remote          │ ← Tap to Optional
│ 🟡 #onsite          │ ← Tap to Optional
└─────────────────────┘

Logic: (#python AND #django) AND (#remote OR #onsite)

Matches:
✅ #python #django #remote
✅ #python #django #onsite
✅ #python #django #remote #onsite
❌ #python #remote
❌ #django #onsite
❌ #remote #onsite
```

## Color Guide

| Icon | Meaning | Logic |
|------|---------|-------|
| ⚪️ | Not set | Ignored in matching |
| 🔴 | Required (AND) | ALL must be present |
| 🟡 | Optional (OR) | At least ONE must be present |

## Tips

1. **Start simple**: Try with 2 required + 2 optional hashtags first
2. **Test it**: Use the Search button to verify your logic works
3. **Required + Optional**: Both groups must match (if set)
4. **No required tags**: Only optional tags will be checked (any match)
5. **No optional tags**: Only required tags will be checked (all match)

## Comparison with Other Modes

| Mode | Logic | Example |
|------|-------|---------|
| **Match ANY** | tag1 OR tag2 OR tag3 | Get messages with at least 1 hashtag |
| **Match ALL** | tag1 AND tag2 AND tag3 | Get messages with all hashtags |
| **Advanced** | (req1 AND req2) AND (opt1 OR opt2) | Custom grouping with AND/OR |
