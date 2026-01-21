# PyQt6 Migration and UI Modernization

## Summary of Changes

This document outlines the changes made to migrate the EEG Quality Check application from PyQt5 to PyQt6 and modernize the user interface.

## Key Changes

### 1. Dependencies Update (requirements.txt)
- **Removed**: PyQt5>=5.15.0, PyQt5-sip>=12.0.0
- **Added**: PyQt6>=6.4.0

### 2. Import Statements (eeg_quality_gui.py)
- Changed all imports from `PyQt5` to `PyQt6`:
  ```python
  # Before:
  from PyQt5.QtWidgets import ...
  from PyQt5.QtCore import ...
  from PyQt5.QtGui import ...
  
  # After:
  from PyQt6.QtWidgets import ...
  from PyQt6.QtCore import ...
  from PyQt6.QtGui import ...
  ```

### 3. Matplotlib Backend Update
- **Changed**: `matplotlib.use('Qt5Agg')` → `matplotlib.use('QtAgg')`
- **Changed**: `from matplotlib.backends.backend_qt5agg import` → `from matplotlib.backends.backend_qtagg import`

### 4. PyQt6 API Changes
- **Font Weight**: Changed `QFont.Bold` to `QFont.Weight.Bold` (PyQt6 uses enum class)
- **Application Execution**: Changed `app.exec_()` to `app.exec()` (underscore removed in PyQt6)

### 5. Dependency Check Update (run_gui.py)
- Updated to check for `PyQt6` instead of `PyQt5`:
  ```python
  # Before:
  import PyQt5
  
  # After:
  import PyQt6
  ```

## UI Modernization

### Enhanced Visual Design
The application now features a modern, professional appearance with:

1. **Color Scheme**
   - Primary colors: Indigo/Purple gradient (#5c6bc0, #7e57c2, #3949ab)
   - Secondary colors: Light blue gradient (#42a5f5, #1e88e5, #1565c0)
   - Background: Light neutral (#f5f7fa)
   - Surfaces: Pure white with subtle shadows

2. **Typography**
   - Increased font weights (600 for emphasis)
   - Larger, more readable font sizes
   - Better hierarchy with the header gradient

3. **Buttons**
   - Gradient backgrounds with smooth transitions
   - Box shadows on hover for depth
   - Increased padding for better touch targets
   - Rounded corners (8px border-radius)

4. **Form Elements**
   - Modern radio button styling with circular indicators
   - Enhanced hover states
   - Better visual feedback

5. **Progress Bar**
   - Gradient fill animation
   - Rounded corners
   - Improved text readability

6. **Tabs**
   - Gradient background for selected tabs
   - Smooth hover transitions
   - Better spacing and padding

7. **Group Boxes**
   - Subtle box shadows for depth
   - Rounded corners (10px)
   - Better visual separation

8. **Header**
   - Gradient background (indigo to purple)
   - White text for better contrast
   - Increased prominence

## Compatibility Notes

### Backward Compatibility
- All existing functionality is preserved
- EEG preprocessing features remain unchanged
- Quality metrics calculations are identical
- File formats and data handling are the same

### System Requirements
- Python 3.8 or higher
- PyQt6 6.4 or higher
- All other dependencies remain the same (MNE, numpy, scipy, matplotlib, etc.)

### Known Limitations
- PyQt6 may require additional system libraries on some platforms
- On headless systems (CI/CD), QT_QPA_PLATFORM=offscreen may be needed
- Some systems may need: libEGL, libGL, libxkbcommon-x11-0

## Installation

### Fresh Installation
```bash
pip install -r requirements.txt
```

### Upgrading from PyQt5
```bash
# Uninstall PyQt5
pip uninstall PyQt5 PyQt5-sip

# Install PyQt6
pip install PyQt6>=6.4.0

# Or install all requirements
pip install -r requirements.txt
```

## Running the Application

The application can be run exactly as before:

```bash
# Using the launcher script
python run_gui.py

# Or directly
python eeg_quality_gui.py
```

## Testing

Automated validation tests have been created to verify the migration:

1. **test_pyqt6_migration.py**: Validates syntax and import correctness
2. **test_gui_structure.py**: Verifies GUI structure and modern features

Run tests:
```bash
python test_pyqt6_migration.py
python test_gui_structure.py
```

## Visual Comparison

### Before (PyQt5)
- Standard green buttons (#4CAF50)
- Flat design with minimal shadows
- Simple tab styling
- Basic color scheme

### After (PyQt6)
- Modern indigo/purple gradient theme
- Depth with shadows and gradients
- Enhanced tab styling with gradients
- Professional color palette
- Improved visual hierarchy

## Technical Details

### Font Weight Enum Change
PyQt6 changed font weights to use an enum class:
```python
# PyQt5:
font = QFont("Arial", 14, QFont.Bold)

# PyQt6:
font = QFont("Arial", 14, QFont.Weight.Bold)
```

### Exec Method Rename
PyQt6 removed the underscore from exec:
```python
# PyQt5:
sys.exit(app.exec_())

# PyQt6:
sys.exit(app.exec())
```

### Matplotlib Backend
PyQt6 uses a generic Qt backend:
```python
# PyQt5:
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

# PyQt6:
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
```

## Future Considerations

### Potential Enhancements
- Dark mode support
- Customizable color themes
- Additional visualization options
- Export to more formats

### Platform-Specific Notes
- **Windows**: PyQt6 should work out of the box
- **macOS**: May need to install via Homebrew for best results
- **Linux**: May need system packages (libegl1, libxcb-xinerama0)

## Support

For issues related to PyQt6 installation or compatibility:
1. Check the PyQt6 documentation: https://www.riverbankcomputing.com/software/pyqt/
2. Verify system requirements
3. Check for missing system libraries
4. Try running with QT_QPA_PLATFORM=offscreen on headless systems

## Version History

### v2.0.0 - PyQt6 Migration
- Migrated from PyQt5 to PyQt6
- Modernized UI with enhanced styling
- Improved visual hierarchy
- Added gradient colors and shadows
- Enhanced user experience

### v1.0.0 - Original Release
- PyQt5-based GUI
- EEG preprocessing and quality metrics
- Traditional and GEDAI methods
