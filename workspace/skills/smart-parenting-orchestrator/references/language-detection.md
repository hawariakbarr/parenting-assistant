# Language Detection Guide

## Indonesian Keywords

**Parenting-related:**
- anak (child)
- bayi (baby)
- balita (toddler)
- sekolah (school)
- hamil (pregnant)
- menyusui (breastfeed)
- tantrum (tantrum)
- rewel (fussy)

**General Indonesian words:**
- bagaimana (how)
- apa (what)
- terima kasih (thank you)
- tolong (help)
- bisa (can)

## English Keywords

**Parenting-related:**
- child, baby, toddler
- school, teacher
- pregnant, pregnancy
- breastfeed, weaning
- behavior, sleep

**Detection Rules:**

1. **High Confidence (>80%):** 3+ keywords in Indonesian
2. **Medium Confidence (50-80%):** 1-2 keywords
3. **Low Confidence (<50%):** No keywords

## Caching

Language detection is cached for **1 hour per session** to avoid repeated detection overhead.

## Override

User can explicitly indicate language preference.
