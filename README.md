# Virus Sandbox

A sophisticated biological simulation game where you design and evolve virtual viruses using genetic engineering principles. Build custom viral genomes, simulate their behavior in biological environments, and compete to achieve evolutionary milestones.

## Overview

Virus Sandbox combines strategic deck-building with real-time biological simulation. Players select genes from a customizable database to engineer viruses, then observe their creations navigate complex biological environments with realistic mechanics including:

- **Entity lifecycle modeling** - Viral particles, RNA, proteins, and other components with natural degradation
- **Transition-based biochemistry** - Genes enable specific biological processes and interactions
- **Interferon immune response** - Dynamic immune system that responds to viral activity
- **Milestone achievement system** - Evolutionary goals with EP (Evolution Points) rewards
- **Gene prerequisite chains** - Realistic dependency relationships between viral components

## Features

### 🧬 Virus Builder
- **Gene Selection**: Choose from a deck of available genes to construct your virus
- **Polymerase Limiting**: Realistic constraint allowing only one polymerase gene per virus
- **Starter Entity Selection**: Choose which viral particle type begins the infection
- **Real-time Validation**: Immediate feedback on gene compatibility and prerequisites

### 🔬 Biological Simulation  
- **Turn-based Evolution**: Step through biological processes turn by turn
- **Entity Type Tracking**: Visual progress bars for virions, RNA, DNA, and proteins
- **Location-based Modeling**: Entities exist in specific cellular compartments (extracellular, cytoplasm, nucleus, etc.)
- **Interferon Dynamics**: Immune response system that affects viral entity degradation
- **Fast-forward Options**: Skip ahead 3 or 10 turns for long simulations

### 📊 Gene Database Editor
- **Entity Management**: Define viral particles, proteins, RNA, and other biological components
- **Gene Effect System**: Create complex biological transitions with multiple inputs/outputs
- **Interferon Configuration**: Set immune response triggers for specific processes
- **Milestone Designer**: Create custom achievement goals with EP rewards
- **JSON Export/Import**: Save and share custom gene databases

### 🎯 Progression System
- **Evolution Points (EP)**: Currency earned through achievements and spent on genes
- **Milestone Tracking**: Survival, entity production, and peak population goals
- **Deck Building**: Expand your gene collection through successful simulations
- **Starting Entity Bonuses**: Skip gene offers to gain more initial viral particles

## Installation & Running

### Prerequisites
- Python 3.8 or higher
- tkinter (included with most Python installations)

### Quick Start
1. Clone or download this repository
2. Navigate to the game directory
3. Run the main game file:
   ```bash
   python viralsandbox.py
   ```

### First Time Setup
1. **Create Sample Database**: From the main menu, click "Create Sample Database" to generate example genes and entities
2. **Start New Game**: Load your sample database to begin playing
3. **Tutorial**: Try the built-in genes to understand basic virus construction

## Gameplay Guide

### Basic Game Loop
1. **Builder Phase**: Select genes from your deck to construct a virus
2. **Simulation Phase**: Watch your virus attempt to survive and replicate
3. **Results Phase**: Earn EP based on performance and milestone achievements
4. **Gene Offer**: Choose new genes for your deck or skip for entity bonuses

### Winning Strategies
- **Balance survivability and growth**: Too aggressive = early extinction, too passive = no progress
- **Understand gene synergies**: Some genes modify others for powerful combinations  
- **Manage your EP economy**: Strategic spending on high-impact genes
- **Milestone planning**: Target specific achievements for maximum EP rewards

### Key Concepts
- **Entity Classes**: Different types (virion, RNA, protein, DNA) have unique properties
- **Degradation Rates**: All entities naturally decay - factor this into your strategy
- **Transition Rules**: Genes enable specific biological processes with probability-based outcomes
- **Interferon Response**: Immune activity increases degradation - some genes trigger this

## File Structure

```
viralsandbox.py          # Main game executable
sample_genes.json        # Example gene database (created by game)
custom_databases/        # Your custom gene databases (created as needed)
```

## Gene Database Format

Gene databases are stored in JSON format with the following structure:

```json
{
  "database_info": {
    "name": "My Database",
    "version": "1.0",
    "description": "Custom genes for advanced play"
  },
  "entities": {
    "entity_name": {
      "name": "entity_name",
      "description": "What this entity represents",
      "base_degradation_rate": 0.05,
      "location": "cytoplasm",
      "entity_class": "RNA",
      "is_starter": false
    }
  },
  "genes": {
    "gene_name": {
      "name": "gene_name",
      "cost": 50,
      "description": "What this gene does",
      "is_polymerase": false,
      "requires": ["prerequisite_gene"],
      "effects": []
    }
  },
  "milestones": {}
}
```

## Advanced Features

### Custom Gene Creation
The built-in editor supports:
- **Multi-input/output transitions**: Complex biochemical reactions
- **Interferon response triggers**: Immune system interaction
- **Probability-based rules**: Realistic biological uncertainty
- **Catalytic processes**: Genes that enable but aren't consumed
- **Rule modifications**: Genes that enhance existing processes

### Milestone System
Create custom achievements targeting:
- **Survival goals**: Keep viruses alive for specific turn counts
- **Peak populations**: Reach maximum entity counts simultaneously  
- **Cumulative production**: Total entities created during simulation
- **Custom rewards**: EP bonuses for completing objectives

## Controls

### Main Interface
- **Mouse**: Navigate menus, select genes, control simulation
- **Enter**: Confirm selections in dialogs
- **Escape**: Cancel dialogs and operations

### Simulation Controls
- **Next Turn**: Advance simulation one turn with detailed logging
- **+3 Turns**: Fast-forward 3 turns instantly
- **+10 Turns**: Fast-forward 10 turns instantly  
- **Return to Builder**: Exit simulation and collect results

## Troubleshooting

### Common Issues
- **Tkinter not found**: Install Python with tkinter support or use `python3-tk` package on Linux
- **Database errors**: Verify JSON syntax in custom databases
- **Performance issues**: Use fast-forward buttons for long simulations instead of individual turns

### Getting Help
- Check the built-in sample database for working examples
- Use the gene editor's validation to identify database issues
- Start with simple gene combinations before attempting complex strategies

## Contributing

This is a single-file Python application using only standard library components. Modifications can be made directly to `viralsandbox.py`. Key areas for extension:

- **New entity types**: Add novel biological components
- **Enhanced AI**: Smarter gene selection algorithms  
- **Multiplayer features**: Compete with custom databases
- **Advanced visualization**: Better simulation graphics
- **Export features**: Save simulation results and statistics

## License

This project is provided as-is for educational and entertainment purposes. Feel free to modify and distribute according to your needs.