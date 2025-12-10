# CLAUDE.md - AI Assistant Guide for JulienCoureau Repository

**Last Updated**: 2025-12-10
**Repository**: JulienCoureau/JulienCoureau
**Project Type**: Personal Website / Portfolio (Static HTML/CSS)

---

## 🎯 Project Overview

This is a personal website/portfolio project for Julien Coureau in its early development stages. The project currently uses vanilla HTML and CSS without any build tools, frameworks, or dependencies.

**Language Context**: The content is in French ("Un super titre" = "A super title").

---

## 📁 Repository Structure

```
JulienCoureau/
├── index.html          # Main HTML page (currently wrapped in styled HTML viewer)
├── styles.css          # Global stylesheet
└── CLAUDE.md           # This file - AI assistant guide
```

### File Descriptions

- **index.html** (2060 bytes)
  - Currently contains HTML code wrapped in an HTML document with inline styling
  - The embedded code shows a basic HTML structure with a link to styles.css
  - Contains French content: "Un super titre"
  - Uses HTML 4.01 Strict DOCTYPE in the wrapper

- **styles.css** (21 bytes)
  - Very minimal styling
  - Currently only styles h1 elements with red color
  - Room for expansion as project grows

---

## 🔧 Development Setup

### Prerequisites
- A web browser (Chrome, Firefox, Safari, etc.)
- A text editor or IDE
- No build tools or package managers required currently

### Running the Project
1. Open `index.html` directly in a web browser
2. Or use a local development server:
   ```bash
   python -m http.server 8000
   # Or
   npx serve .
   ```

### No Dependencies
- No `package.json` or `node_modules`
- No build process required
- No frameworks or libraries in use
- Pure HTML/CSS implementation

---

## 🎨 Development Conventions

### Code Style

**HTML**
- Use semantic HTML5 elements when possible
- Maintain proper indentation (3 spaces based on existing code)
- Keep the French language context for content

**CSS**
- Use clear, descriptive class names
- Follow BEM or similar naming convention as project grows
- Keep styles organized and commented
- Consider mobile-first responsive design

### File Organization
- Keep the flat structure for now given the project's simplicity
- As the project grows, consider organizing into:
  ```
  /css/
  /js/
  /images/
  /assets/
  ```

---

## 🚀 Git Workflow

### Branch Strategy
- Development branches follow pattern: `claude/claude-md-*`
- Current branch: `claude/claude-md-mizsv3qvk8m6y922-01L4tY4fn2WyBkoPSCvjmVgn`

### Commit Messages
- Use clear, descriptive French commit messages (matching existing style)
- Examples from history:
  - "Ajout des fichiers html et css de base"
  - "Ajout du fiichier iindex.html"

### Push Protocol
- Always use: `git push -u origin <branch-name>`
- Branch names must start with `claude/` and end with session ID
- Retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s) on network failures

---

## 🤖 AI Assistant Guidelines

### When Working on This Repository

**DO:**
- ✅ Read existing files before suggesting changes
- ✅ Maintain the French language context for user-facing content
- ✅ Keep solutions simple - this is a beginner-friendly static site
- ✅ Preserve the existing indentation style (3 spaces)
- ✅ Test changes by opening in a browser
- ✅ Write commit messages in French to match existing style
- ✅ Consider accessibility and semantic HTML

**DON'T:**
- ❌ Add unnecessary frameworks or build tools without explicit request
- ❌ Over-engineer simple solutions
- ❌ Add dependencies without discussing with the user
- ❌ Change language from French to English in content
- ❌ Skip reading files before modifying them
- ❌ Create files that aren't explicitly needed

### Common Tasks

#### Adding New Pages
1. Create new `.html` file in root directory
2. Link to `styles.css` stylesheet
3. Use consistent HTML structure with existing pages
4. Add navigation links if needed

#### Updating Styles
1. Read `styles.css` first
2. Add new rules organized by section
3. Keep specificity low for easy overrides
4. Comment complex CSS if added

#### Fixing the Current index.html
**Note**: The current `index.html` appears to be a styled code viewer displaying HTML code. If the intent is to create an actual functional webpage, it should be rewritten to be proper HTML without the wrapper styling.

---

## 📋 Project Roadmap Considerations

As this project grows, consider:

1. **Content Expansion**
   - Add more pages (about, projects, contact)
   - Include a proper navigation menu
   - Add portfolio items or project showcases

2. **Styling Enhancements**
   - Develop a cohesive color scheme
   - Add responsive design for mobile devices
   - Include modern CSS features (Flexbox, Grid)

3. **Assets**
   - Add images, icons, or media
   - Include a favicon
   - Consider web fonts

4. **Optimization** (future)
   - Minification of CSS/HTML
   - Image optimization
   - Performance considerations

5. **Build Tools** (only if needed)
   - Consider tools like Vite or Parcel only when complexity warrants it
   - For now, vanilla HTML/CSS is perfectly fine

---

## 🐛 Known Issues

1. **index.html Structure**: The current file contains HTML code wrapped in a styled HTML document, which may not be the intended structure for a functional website.

---

## 📝 Notes for AI Assistants

### Project Maturity: Early Stage
This is a brand-new project with only 2 commits. Approach it with:
- Simplicity first
- Clear explanations for beginners
- Avoid assumptions about future requirements
- Ask clarifying questions for ambiguous requests

### Language Context
- The owner is French-speaking
- Keep content in French unless explicitly asked to change
- Commit messages should be in French to maintain consistency

### Testing
- Always test HTML changes by opening in a browser
- Verify CSS changes render correctly
- Check responsiveness if adding new features
- Validate HTML/CSS if making significant changes

---

## 🔍 Quick Reference

### Essential Commands
```bash
# View git status
git status

# View recent commits
git log --oneline -5

# Push changes
git push -u origin claude/claude-md-mizsv3qvk8m6y922-01L4tY4fn2WyBkoPSCvjmVgn

# Start local server (if Python available)
python -m http.server 8000
```

### File Locations
- Main page: `/home/user/JulienCoureau/index.html`
- Styles: `/home/user/JulienCoureau/styles.css`
- This guide: `/home/user/JulienCoureau/CLAUDE.md`

---

## 📚 Additional Resources

Since this is a vanilla HTML/CSS project, useful references include:
- [MDN Web Docs](https://developer.mozilla.org/) - HTML/CSS reference
- [Can I Use](https://caniuse.com/) - Browser compatibility
- [W3C Validator](https://validator.w3.org/) - HTML validation
- [CSS Validator](https://jigsaw.w3.org/css-validator/) - CSS validation

---

**Remember**: This is a simple, personal project in early stages. Keep changes focused, simple, and aligned with the user's explicit requests. When in doubt, ask for clarification rather than making assumptions.
