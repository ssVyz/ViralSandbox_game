import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
from abc import ABC, abstractmethod
import random
import json
from copy import deepcopy
import os
from datetime import datetime


# Gene Database Management System
# Gene Database Management System
# Gene Database Management System
class GeneDatabaseManager:
    """Manages loading, saving, and editing gene databases - WITH MILESTONE SUPPORT AND POLYMERASE GENE SUPPORT"""

    def __init__(self):
        self.database = {
            "database_info": {
                "name": "Untitled Database",
                "version": "1.0",
                "description": "",
                "created_by": "User",
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            },
            "entities": {
                "unenveloped virion (extracellular)": {
                    "name": "unenveloped virion (extracellular)",
                    "description": "Basic viral particle outside the cell",
                    "base_degradation_rate": 0.05,
                    "location": "extracellular",
                    "entity_class": "virion",
                    "is_starter": True
                }
            },
            "genes": {},
            "milestones": {}  # Milestone definitions
        }
        self.file_path = None
        self.is_modified = False

    def load_database(self, file_path):
        """Load database from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            # Validate basic structure
            if not self._validate_database_structure(loaded_data):
                raise ValueError("Invalid database structure")

            self.database = loaded_data
            self.file_path = file_path
            self.is_modified = False
            self._ensure_base_entity()
            self._ensure_milestones_section()  # Ensure milestones exist
            self._migrate_genes_add_polymerase_field(loaded_data)  # NEW: Migrate genes for polymerase support
            return True

        except Exception as e:
            raise Exception(f"Failed to load database: {e}")

    def save_database(self, file_path=None):
        """Save database to JSON file"""
        save_path = file_path or self.file_path
        if not save_path:
            raise ValueError("No file path specified")

        # Update metadata
        self.database["database_info"]["last_modified"] = datetime.now().isoformat()

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.database, f, indent=2, ensure_ascii=False)
            self.file_path = save_path
            self.is_modified = False
            return True
        except Exception as e:
            raise Exception(f"Failed to save database: {e}")

    def _validate_database_structure(self, data):
        """Validate that the loaded data has the expected structure"""
        try:
            # Check required top-level keys (milestones is optional for backward compatibility)
            required_keys = ["database_info", "genes", "entities"]
            if not all(key in data for key in required_keys):
                return False

            # Check database_info structure
            info_keys = ["name", "version", "created_date", "last_modified"]
            if not all(key in data["database_info"] for key in info_keys):
                return False

            # Check that genes is a dictionary
            if not isinstance(data["genes"], dict):
                return False

            # Check entities structure - handle both old (list) and new (dict) formats
            if isinstance(data["entities"], list):
                # Old format - migrate to new format
                self._migrate_entities_to_new_format(data)
            elif not isinstance(data["entities"], dict):
                return False

            # Migrate entities to add is_starter field if missing
            self._migrate_entities_add_starter_field(data)

            # NEW: Migrate genes to add is_polymerase field if missing
            self._migrate_genes_add_polymerase_field(data)

            # Ensure milestones section exists (migration)
            if "milestones" not in data:
                data["milestones"] = {}
            elif not isinstance(data["milestones"], dict):
                data["milestones"] = {}

            return True
        except:
            return False

    def _ensure_milestones_section(self):
        """Ensure milestones section exists in database"""
        if "milestones" not in self.database:
            self.database["milestones"] = {}
            self.is_modified = True

    def _migrate_entities_to_new_format(self, data):
        """Migrate old entities list format to new entities object format"""
        if isinstance(data["entities"], list):
            old_entities = data["entities"]
            new_entities = {}

            for entity_name in old_entities:
                new_entities[entity_name] = {
                    "name": entity_name,
                    "description": f"Auto-migrated entity: {entity_name}",
                    "base_degradation_rate": 0.05,  # Default degradation rate
                    "location": self._guess_location_from_name(entity_name),
                    "entity_class": self._guess_class_from_name(entity_name),
                    "is_starter": entity_name == "unenveloped virion (extracellular)"
                }

            data["entities"] = new_entities

    def _migrate_entities_add_starter_field(self, data):
        """Add is_starter field to entities that don't have it"""
        if "entities" in data and isinstance(data["entities"], dict):
            for entity_name, entity_data in data["entities"].items():
                if "is_starter" not in entity_data:
                    # Mark the default base entity as starter, others as non-starter
                    if entity_name == "unenveloped virion (extracellular)":
                        entity_data["is_starter"] = True
                    else:
                        entity_data["is_starter"] = False

    def _migrate_genes_add_polymerase_field(self, data):
        """Add is_polymerase field to genes that don't have it - NEW METHOD"""
        if "genes" in data and isinstance(data["genes"], dict):
            for gene_name, gene_data in data["genes"].items():
                if "is_polymerase" not in gene_data:
                    # Default all existing genes to non-polymerase for backward compatibility
                    gene_data["is_polymerase"] = False
            # Mark as modified if we made any changes
            if any("is_polymerase" not in gene for gene in data["genes"].values()):
                self.is_modified = True

    def _guess_location_from_name(self, entity_name):
        """Guess location from entity name"""
        name_lower = entity_name.lower()
        if "(extracellular)" in name_lower:
            return "extracellular"
        elif "(cytoplasm)" in name_lower:
            return "cytoplasm"
        elif "(endosome)" in name_lower:
            return "endosome"
        elif "(nucleus)" in name_lower:
            return "nucleus"
        else:
            return "unknown"

    def _guess_class_from_name(self, entity_name):
        """Guess entity class from name"""
        name_lower = entity_name.lower()
        if "rna" in name_lower:
            return "RNA"
        elif any(term in name_lower for term in ["protein", "polymerase", "protease"]):
            return "protein"
        elif "virion" in name_lower:
            return "virion"
        else:
            return "unknown"

    def _ensure_base_entity(self):
        """Ensure the base entity exists"""
        base_entity_name = "unenveloped virion (extracellular)"
        if base_entity_name not in self.database["entities"]:
            self.database["entities"][base_entity_name] = {
                "name": base_entity_name,
                "description": "Basic viral particle outside the cell",
                "base_degradation_rate": 0.05,
                "location": "extracellular",
                "entity_class": "virion",
                "is_starter": True
            }

    def add_entity(self, entity_data):
        """Add or update an entity"""
        entity_name = entity_data["name"]
        # Ensure is_starter field exists with default value if not provided
        if "is_starter" not in entity_data:
            entity_data["is_starter"] = False

        self.database["entities"][entity_name] = entity_data.copy()
        self.is_modified = True

    def delete_entity(self, entity_name):
        """Delete an entity"""
        if entity_name in self.database["entities"]:
            del self.database["entities"][entity_name]
            self.is_modified = True

    def get_entity(self, entity_name):
        """Get an entity by name"""
        return self.database["entities"].get(entity_name)

    def get_all_entity_names(self):
        """Get all entity names"""
        return list(self.database["entities"].keys())

    def get_entities(self):
        """Get all entities as a dict"""
        return self.database["entities"].copy()

    def get_starter_entities(self):
        """Get all entities marked as starter entities"""
        starter_entities = []
        for entity_name, entity_data in self.database["entities"].items():
            if entity_data.get("is_starter", False):
                starter_entities.append(entity_name)
        return starter_entities

    def get_starter_entity_names(self):
        """Get names of all starter entities (alias for compatibility)"""
        return self.get_starter_entities()

    def set_entity_starter_status(self, entity_name, is_starter):
        """Set the starter status of an entity"""
        if entity_name in self.database["entities"]:
            self.database["entities"][entity_name]["is_starter"] = bool(is_starter)
            self.is_modified = True
            return True
        return False

    def add_gene(self, gene_data):
        """Add or update a gene - UPDATED WITH POLYMERASE SUPPORT"""
        gene_name = gene_data["name"]

        # Ensure is_polymerase field exists with default value if not provided
        if "is_polymerase" not in gene_data:
            gene_data["is_polymerase"] = False

        self.database["genes"][gene_name] = gene_data.copy()
        self._update_entities_from_genes()
        self.is_modified = True

    def delete_gene(self, gene_name):
        """Delete a gene"""
        if gene_name in self.database["genes"]:
            del self.database["genes"][gene_name]
            self._update_entities_from_genes()
            self.is_modified = True

    def get_gene(self, gene_name):
        """Get a gene by name"""
        gene_data = self.database["genes"].get(gene_name)
        if gene_data and "is_polymerase" not in gene_data:
            # Ensure backward compatibility - add missing polymerase field
            gene_data["is_polymerase"] = False
        return gene_data

    def get_all_genes(self):
        """Get all gene names"""
        return list(self.database["genes"].keys())

    def get_polymerase_genes(self):
        """Get all genes marked as polymerase genes - NEW METHOD"""
        polymerase_genes = []
        for gene_name, gene_data in self.database["genes"].items():
            if gene_data.get("is_polymerase", False):
                polymerase_genes.append(gene_name)
        return polymerase_genes

    def is_polymerase_gene(self, gene_name):
        """Check if a gene is marked as a polymerase gene - NEW METHOD"""
        gene_data = self.database["genes"].get(gene_name)
        if gene_data:
            return gene_data.get("is_polymerase", False)
        return False

    def _update_entities_from_genes(self):
        """Update entities list based on genes (for backwards compatibility)"""
        # This method ensures all entities referenced in genes exist as proper entity objects
        referenced_entities = set()

        for gene in self.database["genes"].values():
            for effect in gene.get("effects", []):
                if effect["type"] == "enable_entity":
                    referenced_entities.add(effect["entity"])
                elif effect["type"] in ["add_transition"]:
                    rule = effect["rule"]
                    for input_spec in rule["inputs"]:
                        referenced_entities.add(input_spec["entity"])
                    for output_spec in rule["outputs"]:
                        referenced_entities.add(output_spec["entity"])

        # Add any missing entities as basic entities
        for entity_name in referenced_entities:
            if entity_name not in self.database["entities"]:
                self.database["entities"][entity_name] = {
                    "name": entity_name,
                    "description": f"Auto-generated entity: {entity_name}",
                    "base_degradation_rate": 0.05,
                    "location": self._guess_location_from_name(entity_name),
                    "entity_class": self._guess_class_from_name(entity_name),
                    "is_starter": False
                }

    # =================== MILESTONE MANAGEMENT ===================

    def add_milestone(self, milestone_data):
        """Add or update a milestone"""
        milestone_id = milestone_data["id"]
        self.database["milestones"][milestone_id] = milestone_data.copy()
        self.is_modified = True

    def delete_milestone(self, milestone_id):
        """Delete a milestone"""
        if milestone_id in self.database["milestones"]:
            del self.database["milestones"][milestone_id]
            self.is_modified = True

    def get_milestone(self, milestone_id):
        """Get a milestone by ID"""
        return self.database["milestones"].get(milestone_id)

    def get_all_milestones(self):
        """Get all milestone IDs"""
        return list(self.database["milestones"].keys())

    def get_milestones(self):
        """Get all milestones as a dict"""
        return self.database["milestones"].copy()

    def get_entity_classes(self):
        """Get all unique entity classes defined in the database"""
        classes = set()
        for entity_data in self.database["entities"].values():
            entity_class = entity_data.get("entity_class", "unknown")
            if entity_class:
                classes.add(entity_class)
        return sorted(list(classes))

    def validate_milestone_data(self, milestone_data):
        """Validate milestone data structure and values"""
        required_fields = ["id", "name", "description", "type", "target", "reward_ep"]

        # Check required fields
        for field in required_fields:
            if field not in milestone_data:
                return False, f"Missing required field: {field}"

        # Validate milestone ID (no spaces, alphanumeric + underscore)
        milestone_id = milestone_data["id"]
        if not milestone_id.replace("_", "").replace("-", "").isalnum():
            return False, "Milestone ID must contain only letters, numbers, underscores, and hyphens"

        # Validate milestone type
        valid_types = ["survive_turns", "peak_entity_count", "cumulative_entity_count"]
        if milestone_data["type"] not in valid_types:
            return False, f"Invalid milestone type. Must be one of: {', '.join(valid_types)}"

        # Validate target (must be positive integer)
        try:
            target = int(milestone_data["target"])
            if target <= 0:
                return False, "Target must be a positive integer"
        except (ValueError, TypeError):
            return False, "Target must be a valid positive integer"

        # Validate reward_ep (must be non-negative integer)
        try:
            reward = int(milestone_data["reward_ep"])
            if reward < 0:
                return False, "Reward EP must be a non-negative integer"
        except (ValueError, TypeError):
            return False, "Reward EP must be a valid non-negative integer"

        # Validate entity_class for entity count milestones
        if milestone_data["type"] in ["peak_entity_count", "cumulative_entity_count"]:
            if "entity_class" not in milestone_data:
                return False, "Entity count milestones must specify an entity_class"

            available_classes = self.get_entity_classes()
            if milestone_data["entity_class"] not in available_classes:
                return False, f"Invalid entity_class. Available classes: {', '.join(available_classes)}"

        return True, "Valid milestone data"

    def create_sample_database(self):
        """Create a sample database with a few example genes and milestones - UPDATED TO REMOVE PRODUCTION AND ADD POLYMERASE FLAGS"""
        self.database = {
            "database_info": {
                "name": "Sample Virus Gene Database",
                "version": "1.0",
                "description": "Sample database with basic viral genes and milestones demonstrating different effect types",
                "created_by": "Virus Sandbox",
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            },
            "entities": {
                "unenveloped virion (extracellular)": {
                    "name": "unenveloped virion (extracellular)",
                    "description": "Basic viral particle outside the cell",
                    "base_degradation_rate": 0.05,
                    "location": "extracellular",
                    "entity_class": "virion",
                    "is_starter": True
                },
                "enveloped virion (extracellular)": {
                    "name": "enveloped virion (extracellular)",
                    "description": "Viral particle with lipid envelope outside the cell",
                    "base_degradation_rate": 0.08,
                    "location": "extracellular",
                    "entity_class": "virion",
                    "is_starter": True
                },
                "viral spore (extracellular)": {
                    "name": "viral spore (extracellular)",
                    "description": "Dormant viral form with enhanced environmental resistance",
                    "base_degradation_rate": 0.02,
                    "location": "extracellular",
                    "entity_class": "virion",
                    "is_starter": True
                },
                "virion in endosome (cytoplasm)": {
                    "name": "virion in endosome (cytoplasm)",
                    "description": "Viral particle inside cellular endosome",
                    "base_degradation_rate": 0.03,
                    "location": "endosome",
                    "entity_class": "virion",
                    "is_starter": False
                },
                "viral polymerase (cytoplasm)": {
                    "name": "viral polymerase (cytoplasm)",
                    "description": "Viral RNA polymerase enzyme in cytoplasm",
                    "base_degradation_rate": 0.08,
                    "location": "cytoplasm",
                    "entity_class": "protein",
                    "is_starter": False
                },
                "viral RNA (cytoplasm)": {
                    "name": "viral RNA (cytoplasm)",
                    "description": "Viral genetic material in cytoplasm",
                    "base_degradation_rate": 0.12,
                    "location": "cytoplasm",
                    "entity_class": "RNA",
                    "is_starter": False
                },
                "mature viral proteins (cytoplasm)": {
                    "name": "mature viral proteins (cytoplasm)",
                    "description": "Processed viral proteins ready for assembly",
                    "base_degradation_rate": 0.06,
                    "location": "cytoplasm",
                    "entity_class": "protein",
                    "is_starter": False
                }
            },
            "genes": {
                "Basic Capsid": {
                    "name": "Basic Capsid",
                    "cost": 0,
                    "description": "Basic viral capsid protein. Provides structural integrity.",
                    "effects": [],
                    "is_polymerase": False  # NEW: Explicit polymerase flag
                },
                "Glycoprotein S1": {
                    "name": "Glycoprotein S1",
                    "cost": 50,
                    "description": "Surface protein enabling receptor binding and endocytosis",
                    "effects": [
                        {
                            "type": "add_transition",
                            "rule": {
                                "name": "Receptor-mediated endocytosis",
                                "inputs": [
                                    {"entity": "unenveloped virion (extracellular)", "count": 1, "consumed": True}],
                                "outputs": [{"entity": "virion in endosome (cytoplasm)", "count": 1}],
                                "probability": 0.3,
                                "rule_type": "per_entity"
                            }
                        }
                    ],
                    "is_polymerase": False  # NEW: Explicit polymerase flag
                },
                "RNA-dependent RNA polymerase": {
                    "name": "RNA-dependent RNA polymerase",
                    "cost": 80,
                    "description": "Enzyme enabling viral RNA replication in the cytoplasm",
                    "effects": [
                        {
                            "type": "add_transition",
                            "rule": {
                                "name": "RNA replication",
                                "inputs": [
                                    {"entity": "viral polymerase (cytoplasm)", "count": 1, "consumed": False},
                                    {"entity": "viral RNA (cytoplasm)", "count": 1, "consumed": False}
                                ],
                                "outputs": [{"entity": "viral RNA (cytoplasm)", "count": 1}],
                                "probability": 0.7,
                                "rule_type": "per_pair"
                            }
                        }
                    ],
                    "is_polymerase": True  # NEW: This is marked as a polymerase gene!
                },
                "Membrane fusion protein": {
                    "name": "Membrane fusion protein",
                    "cost": 60,
                    "description": "Protein that enables escape from endosomes",
                    "requires": ["Glycoprotein S1"],
                    "effects": [
                        {
                            "type": "add_transition",
                            "rule": {
                                "name": "Endosome escape",
                                "inputs": [{"entity": "virion in endosome (cytoplasm)", "count": 1, "consumed": True}],
                                "outputs": [
                                    {"entity": "viral RNA (cytoplasm)", "count": 2},
                                    {"entity": "viral polymerase (cytoplasm)", "count": 1}
                                ],
                                "probability": 0.8,
                                "rule_type": "per_entity"
                            }
                        }
                    ],
                    "is_polymerase": False  # NEW: Explicit polymerase flag
                },
                "Enhanced glycoprotein S1": {
                    "name": "Enhanced glycoprotein S1",
                    "cost": 30,
                    "description": "Improved version with higher binding affinity",
                    "requires": ["Glycoprotein S1"],
                    "effects": [
                        {
                            "type": "modify_transition",
                            "rule_name": "Receptor-mediated endocytosis",
                            "modification": {
                                "probability_multiplier": 1.5
                            }
                        }
                    ],
                    "is_polymerase": False  # NEW: Explicit polymerase flag
                },
                "Viral protease": {
                    "name": "Viral protease",
                    "cost": 40,
                    "description": "Enzyme that processes viral proteins",
                    "effects": [
                        {
                            "type": "add_transition",
                            "rule": {
                                "name": "Protein maturation",
                                "inputs": [{"entity": "viral polymerase (cytoplasm)", "count": 1, "consumed": True}],
                                "outputs": [{"entity": "mature viral proteins (cytoplasm)", "count": 2}],
                                "probability": 0.9,
                                "rule_type": "per_entity"
                            }
                        }
                    ],
                    "is_polymerase": False  # NEW: Explicit polymerase flag
                }
            },
            # Sample milestones
            "milestones": {
                "survivor_5": {
                    "id": "survivor_5",
                    "name": "Basic Survival",
                    "description": "Keep your virus alive for at least 5 turns",
                    "type": "survive_turns",
                    "target": 5,
                    "reward_ep": 25
                },
                "survivor_15": {
                    "id": "survivor_15",
                    "name": "Extended Survival",
                    "description": "Keep your virus alive for at least 15 turns",
                    "type": "survive_turns",
                    "target": 15,
                    "reward_ep": 75
                },
                "protein_peak_10": {
                    "id": "protein_peak_10",
                    "name": "Protein Factory",
                    "description": "Have 10 protein entities present at the same time",
                    "type": "peak_entity_count",
                    "entity_class": "protein",
                    "target": 10,
                    "reward_ep": 50
                },
                "rna_cumulative_25": {
                    "id": "rna_cumulative_25",
                    "name": "RNA Production Line",
                    "description": "Create a total of 25 RNA entities during the simulation",
                    "type": "cumulative_entity_count",
                    "entity_class": "RNA",
                    "target": 25,
                    "reward_ep": 60
                },
                "virion_peak_20": {
                    "id": "virion_peak_20",
                    "name": "Viral Swarm",
                    "description": "Have 20 virion entities present at the same time",
                    "type": "peak_entity_count",
                    "entity_class": "virion",
                    "target": 20,
                    "reward_ep": 100
                }
            }
        }
        self.is_modified = True


class GeneDatabase:
    """Interface to gene database for virus building"""

    def __init__(self, database_manager=None):
        self.db_manager = database_manager

    def set_database_manager(self, database_manager):
        """Set the database manager"""
        self.db_manager = database_manager

    def get_gene(self, name):
        """Get a gene by name"""
        if not self.db_manager:
            return None
        return self.db_manager.get_gene(name)

    def get_all_genes(self):
        """Get all gene names"""
        if not self.db_manager:
            return []
        return self.db_manager.get_all_genes()

    def get_available_genes(self, selected_genes):
        """Get genes that can be selected given current selection"""
        if not self.db_manager:
            return []

        available = []
        selected_gene_names = [gene["name"] for gene in selected_genes]

        for gene_name in self.db_manager.get_all_genes():
            if gene_name in selected_gene_names:
                continue  # Already selected

            gene_data = self.db_manager.get_gene(gene_name)
            if not gene_data:
                continue

            # Check prerequisites
            requires = gene_data.get("requires", [])
            if all(req in selected_gene_names for req in requires):
                available.append(gene_name)

        return available


class VirusBuilder:
    """Builds virus configurations from selected genes - UPDATED WITH DYNAMIC STARTER ENTITY, INTERFERON SUPPORT, AND POLYMERASE LIMITING"""

    BIG_BUDGET = 1_000_000  # neutralize legacy budget checks

    def __init__(self, gene_database, game_state=None):
        self.gene_db = gene_database
        self.game_state = game_state  # Reference to game state for starter entity
        self.base_entities = ["unenveloped virion (extracellular)"]  # Legacy fallback
        self.selected_genes = []
        self.budget = 200
        self.spent = 0

    def set_game_state(self, game_state):
        """Set game state reference"""
        self.game_state = game_state

    def get_starter_entity(self):
        """Get the current starter entity"""
        if self.game_state:
            return self.game_state.get_selected_starter_entity()
        else:
            # Fallback to legacy behavior
            return self.base_entities[0]

    def can_afford_gene(self, gene_name):
        gene = self.gene_db.get_gene(gene_name)
        return gene and (self.spent + gene["cost"]) <= self.budget

    def can_add_gene(self, gene_name):
        """
        Non-mutating validation for whether a gene can be added.
        Returns (ok: bool, reason: str) where reason is a short tag you can branch on.
        """
        gene = self.gene_db.get_gene(gene_name)
        if not gene:
            return False, "unknown_gene"

        # Legacy builder budget (neutralized via BIG_BUDGET, but keep check for consistency)
        if not self.can_afford_gene(gene_name):
            return False, "builder_budget"

        # Already installed?
        if any(g["name"] == gene_name for g in self.selected_genes):
            return False, "already_installed"

        # Prerequisites
        requires = gene.get("requires", [])
        selected_names = [g["name"] for g in self.selected_genes]
        if not all(req in selected_names for req in requires):
            return False, "missing_prerequisites"

        # Polymerase limit
        if gene.get("is_polymerase", False) and self._has_polymerase_gene():
            return False, "polymerase_limit"

        return True, ""

    def add_gene(self, gene_name):
        """Add a gene to the virus - UPDATED WITH POLYMERASE LIMITING"""
        gene = self.gene_db.get_gene(gene_name)
        if not gene:
            return False

        if not self.can_afford_gene(gene_name):
            return False

        # Check if already selected
        if any(g["name"] == gene_name for g in self.selected_genes):
            return False

        # Check prerequisites
        requires = gene.get("requires", [])
        selected_names = [g["name"] for g in self.selected_genes]
        if not all(req in selected_names for req in requires):
            return False

        # NEW: Check polymerase gene limitation
        if gene.get("is_polymerase", False):
            if self._has_polymerase_gene():
                # Already have a polymerase gene - cannot add another
                return False

        self.selected_genes.append(gene)
        self.spent += gene["cost"]
        return True

    def remove_gene(self, gene_name):
        """Remove a gene from the virus"""
        # Remove the gene and any genes that depend on it
        to_remove = []

        # Find genes that depend on this one
        for gene in self.selected_genes:
            if gene_name in gene.get("requires", []):
                to_remove.append(gene["name"])

        # Remove dependent genes first
        for dep_gene in to_remove:
            self.remove_gene(dep_gene)

        # Remove the gene itself
        for i, gene in enumerate(self.selected_genes):
            if gene["name"] == gene_name:
                self.spent -= gene["cost"]
                del self.selected_genes[i]
                break

    def _has_polymerase_gene(self):
        """Check if there's already a polymerase gene in the selected genes - NEW METHOD"""
        return any(gene.get("is_polymerase", False) for gene in self.selected_genes)

    def get_selected_polymerase_gene(self):
        """Get the name of the currently selected polymerase gene, or None - NEW METHOD"""
        for gene in self.selected_genes:
            if gene.get("is_polymerase", False):
                return gene["name"]
        return None

    def count_polymerase_genes(self):
        """Count the number of polymerase genes currently selected - NEW METHOD"""
        return sum(1 for gene in self.selected_genes if gene.get("is_polymerase", False))

    def get_virus_capabilities(self):
        """Get the full virus configuration - UPDATED WITH INTERFERON SUPPORT"""
        available_entities = set()
        transition_rules = []

        # Use dynamic starter entity instead of hardcoded one
        starter_entity_name = self.get_starter_entity()
        available_entities.add(starter_entity_name)

        for gene in self.selected_genes:
            for effect in gene["effects"]:
                if effect["type"] in ["add_transition", "add_production"]:
                    rule = effect["rule"].copy()  # Make a copy to avoid modifying original

                    # Add entities referenced in this rule
                    for input_spec in rule["inputs"]:
                        available_entities.add(input_spec["entity"])
                    for output_spec in rule["outputs"]:
                        available_entities.add(output_spec["entity"])

                    # Copy interferon amount if present
                    if "interferon_amount" in rule:
                        # Ensure it's a float with proper precision
                        rule["interferon_amount"] = round(float(rule.get("interferon_amount", 0.0)), 2)

                    transition_rules.append(rule)

                elif effect["type"] == "modify_transition":
                    # Find and modify existing rule
                    rule_name = effect["rule_name"]
                    modification = effect.get("modification", {})

                    for rule in transition_rules:
                        if rule["name"] == rule_name:
                            # Apply probability multiplier (existing functionality)
                            if "probability_multiplier" in modification:
                                rule["probability"] *= modification["probability_multiplier"]
                                rule["probability"] = min(1.0, rule["probability"])  # Cap at 100%

                            # Apply interferon multiplier
                            if "interferon_multiplier" in modification:
                                current_interferon = rule.get("interferon_amount", 0.0)
                                if current_interferon > 0:  # Only modify if rule actually has interferon
                                    new_interferon = current_interferon * modification["interferon_multiplier"]
                                    rule["interferon_amount"] = round(new_interferon, 2)

        # Get degradation rates for all entities
        entity_degradation_rates = {}
        if self.gene_db and self.gene_db.db_manager:
            for entity_name in available_entities:
                entity_data = self.gene_db.db_manager.get_entity(entity_name)
                if entity_data:
                    entity_degradation_rates[entity_name] = entity_data.get("base_degradation_rate", 0.05)
                else:
                    entity_degradation_rates[entity_name] = 0.05  # Default fallback
        else:
            # Fallback if no database manager
            for entity_name in available_entities:
                entity_degradation_rates[entity_name] = 0.05

        # Get dynamic starting entity count from game state
        starting_count = 10  # Default fallback
        if self.game_state:
            starting_count = self.game_state.get_starting_entity_count()

        return {
            "starting_entities": {starter_entity_name: starting_count},  # Dynamic starting count
            "possible_entities": list(available_entities),
            "transition_rules": transition_rules,  # Now includes interferon_amount fields
            "genes": [gene["name"] for gene in self.selected_genes],
            "entity_degradation_rates": entity_degradation_rates  # Degradation rates
        }


class ViralSimulation:
    """Handles the actual virus simulation - UPDATED WITH INTERFERON MECHANIC"""

    def __init__(self, virus_blueprint):
        self.entities = virus_blueprint["starting_entities"].copy()
        self.transition_rules = virus_blueprint["transition_rules"]
        self.degradation_rates = virus_blueprint.get("entity_degradation_rates", {})
        self.db_manager = None  # Will be set by PlayModule for location data
        self.turn_count = 0
        self.console_log = []

        # NEW: Interferon system
        self.interferon_level = 0.0  # Float with 2 decimal precision, starts at 0

    def process_turn(self):
        """Process one simulation turn - UPDATED WITH INTERFERON DECAY"""
        self.turn_count += 1
        starting_entities = self.entities.copy()
        changes = []

        # Apply degradation first, before any transition rules (now includes interferon effects)
        degradation_changes = self.apply_degradation(starting_entities)
        changes.extend(degradation_changes)

        # Apply degradation to working state so degraded entities can't participate in transitions
        working_entities = starting_entities.copy()
        for change in degradation_changes:
            if change["type"] == "degraded":
                entity_name = change["entity"]
                count = change["count"]
                working_entities[entity_name] -= count
                if working_entities[entity_name] <= 0:
                    del working_entities[entity_name]

        # Process each transition rule against the post-degradation state (now includes interferon generation)
        interferon_added_this_turn = 0.0
        for rule in self.transition_rules:
            rule_changes = self.apply_rule_to_state(rule, working_entities)
            changes.extend(rule_changes)

            # NEW: Check for interferon effects in this rule
            interferon_added = self._process_rule_interferon_effects(rule, rule_changes)
            if interferon_added > 0:
                interferon_added_this_turn += interferon_added

            # Update working state with consumed entities only
            # (so we don't double-consume the same entities)
            for change in rule_changes:
                if change["type"] == "consumed":
                    entity_name = change["entity"]
                    count = change["count"]
                    working_entities[entity_name] -= count
                    if working_entities[entity_name] <= 0:
                        del working_entities[entity_name]

        # NEW: Apply interferon decay (decrease by 1.0 per turn)
        self.interferon_level = max(0.0, self.interferon_level - 1.0)

        # NEW: Add interferon generated this turn (cap at 100.0)
        if interferon_added_this_turn > 0:
            self.interferon_level = min(100.0, self.interferon_level + interferon_added_this_turn)

        # Apply all changes at once (including degradation)
        self.apply_all_changes(changes)

        # Generate console log (now includes interferon status)
        turn_log = self.generate_turn_log(starting_entities, changes, interferon_added_this_turn)
        self.console_log.extend(turn_log)

        return turn_log

    def _estimate_applications_from_changes(self, rule, rule_changes):
        """
        Estimate how many times a rule actually applied in this turn:
        1) Prefer consumed inputs (if any and present in changes),
        2) otherwise derive from produced outputs.
        """
        # 1) Try from consumed inputs
        consumed_counts = {}
        for ch in rule_changes:
            if ch["type"] == "consumed":
                consumed_counts[ch["entity"]] = consumed_counts.get(ch["entity"], 0) + ch["count"]

        apps_from_consumed = None
        if rule.get("inputs"):
            consumed_inputs = [i for i in rule["inputs"] if i.get("consumed", True)]
            if consumed_inputs and consumed_counts:
                vals = []
                for i in consumed_inputs:
                    per_app = max(1, int(i.get("count", 1)))
                    have = int(consumed_counts.get(i["entity"], 0))
                    vals.append(have // per_app)
                if vals:
                    apps_from_consumed = min(vals)

        if apps_from_consumed:
            return int(apps_from_consumed)

        # 2) Fall back to produced outputs (covers catalytic/non-consuming rules)
        produced_counts = {}
        for ch in rule_changes:
            if ch["type"] == "produced":
                produced_counts[ch["entity"]] = produced_counts.get(ch["entity"], 0) + ch["count"]

        if rule.get("outputs") and produced_counts:
            vals = []
            for o in rule["outputs"]:
                per_app = max(1, int(o.get("count", 1)))
                made = int(produced_counts.get(o["entity"], 0))
                vals.append(made // per_app)
            if vals:
                return int(min(vals))

        # No signal → treat as zero
        return 0

    def _process_rule_interferon_effects(self, rule, rule_changes):
        """Process interferon effects for a rule based on its successful applications"""
        interferon_amount = float(rule.get("interferon_amount", 0.0) or 0.0)
        if interferon_amount <= 0:
            return 0.0

        successful_applications = self._estimate_applications_from_changes(rule, rule_changes)
        total_interferon = successful_applications * interferon_amount
        return round(total_interferon, 2)

    def apply_degradation(self, entity_state):
        """Apply degradation to entities based on their degradation rates AND interferon levels"""
        import random
        degradation_changes = []

        for entity_name, count in entity_state.items():
            if count <= 0:
                continue

            # Get base degradation rate for this entity
            base_degradation_rate = self.degradation_rates.get(entity_name, 0.05)

            # NEW: Calculate interferon-based degradation bonus
            interferon_bonus = self._calculate_interferon_degradation_bonus(entity_name)

            # Final degradation rate (capped at 1.0 = 100%)
            final_degradation_rate = min(1.0, base_degradation_rate * (1.0 + interferon_bonus))

            if final_degradation_rate <= 0:
                continue  # No degradation

            # Apply degradation: each individual entity has a chance to degrade
            degraded_count = 0
            for _ in range(count):
                if random.random() < final_degradation_rate:
                    degraded_count += 1

            if degraded_count > 0:
                degradation_changes.append({
                    "type": "degraded",
                    "entity": entity_name,
                    "count": degraded_count,
                    "rule_name": "Natural degradation"
                })

        return degradation_changes

    def _calculate_interferon_degradation_bonus(self, entity_name):
        """Calculate additional degradation rate due to interferon for a specific entity"""
        if self.interferon_level <= 0 or not self.db_manager:
            return 0.0

        # Get entity class from database
        entity_data = self.db_manager.get_entity(entity_name)
        if not entity_data:
            return 0.0

        entity_class = entity_data.get("entity_class", "").lower()

        # Apply interferon degradation bonuses based on entity class
        interferon_multipliers = {
            "rna": 0.0125,  # 1% increased degradation per interferon level
            "protein": 0.0075,  # 0.5% increased degradation per interferon level
            "dna": 0.005  # 0.2% increased degradation per interferon level
        }

        multiplier = interferon_multipliers.get(entity_class, 0.0)
        bonus = self.interferon_level * multiplier

        return round(bonus, 4)  # Round to 4 decimals for precision in degradation calculations

    def apply_rule_to_state(self, rule, entity_state):
        """Apply a single transition rule to a given entity state (doesn't modify self.entities)"""
        max_applications = self.get_max_applications_from_state(rule, entity_state)
        if max_applications == 0:
            return []

        # Calculate actual applications based on probability
        if rule["rule_type"] == "per_entity":
            actual_applications = sum(1 for _ in range(max_applications)
                                      if random.random() < rule["probability"])
        elif rule["rule_type"] == "per_pair":
            actual_applications = sum(1 for _ in range(max_applications)
                                      if random.random() < rule["probability"])
        else:
            actual_applications = 0

        if actual_applications == 0:
            return []

        changes = []

        # Record consumed inputs
        for input_spec in rule["inputs"]:
            if input_spec["consumed"]:
                consumed = actual_applications * input_spec["count"]
                entity_name = input_spec["entity"]

                changes.append({
                    "type": "consumed",
                    "entity": entity_name,
                    "count": consumed,
                    "rule_name": rule["name"]
                })

        # Record produced outputs
        for output_spec in rule["outputs"]:
            produced = actual_applications * output_spec["count"]
            entity_name = output_spec["entity"]

            changes.append({
                "type": "produced",
                "entity": entity_name,
                "count": produced,
                "rule_name": rule["name"]
            })

        return changes

    def get_max_applications_from_state(self, rule, entity_state):
        """Calculate maximum times rule can be applied from a given state"""
        max_apps = float('inf')

        for input_spec in rule["inputs"]:
            entity_name = input_spec["entity"]
            required_count = input_spec["count"]
            available = entity_state.get(entity_name, 0)

            if available < required_count:
                return 0  # Can't apply at all

            if input_spec["consumed"]:
                max_apps = min(max_apps, available // required_count)
            else:
                # For production rules, each set of inputs can produce once
                max_apps = min(max_apps, available // required_count)

        return max_apps if max_apps != float('inf') else 0

    def apply_all_changes(self, changes):
        """Apply all accumulated changes to the entity state - UPDATED TO HANDLE DEGRADATION"""
        # Group changes by type and entity
        consumed = {}
        produced = {}
        degraded = {}

        for change in changes:
            entity_name = change["entity"]
            count = change["count"]

            if change["type"] == "consumed":
                consumed[entity_name] = consumed.get(entity_name, 0) + count
            elif change["type"] == "produced":
                produced[entity_name] = produced.get(entity_name, 0) + count
            elif change["type"] == "degraded":  # Handle degradation
                degraded[entity_name] = degraded.get(entity_name, 0) + count

        # Apply degraded changes (similar to consumed)
        for entity_name, count in degraded.items():
            if entity_name in self.entities:
                self.entities[entity_name] -= count
                if self.entities[entity_name] <= 0:
                    del self.entities[entity_name]

        # Apply consumed changes
        for entity_name, count in consumed.items():
            if entity_name in self.entities:
                self.entities[entity_name] -= count
                if self.entities[entity_name] <= 0:
                    del self.entities[entity_name]

        # Apply produced changes
        for entity_name, count in produced.items():
            if entity_name in self.entities:
                self.entities[entity_name] += count
            else:
                self.entities[entity_name] = count

    def generate_turn_log(self, starting_entities, changes, interferon_added_this_turn=0.0):
        """Generate console log for this turn - UPDATED WITH INTERFERON STATUS"""
        log_entries = []

        # Turn header - Clear visual separation
        if self.turn_count == 1:
            log_entries.append("=" * 70)
            log_entries.append("  SIMULATION START")
            log_entries.append("=" * 70)
        else:
            log_entries.append("")
            log_entries.append("-" * 70)

        log_entries.append(f"  TURN {self.turn_count}")
        log_entries.append("-" * 70)

        # EVENTS SECTION - Process and display in logical order WITH ENHANCED MULTI-ENTITY FORMATTING
        if changes:
            log_entries.append("")
            log_entries.append("  Events this turn:")

            # Group changes by rule and type for better organization
            rule_changes = {}
            for change in changes:
                rule_name = change["rule_name"]
                if rule_name not in rule_changes:
                    rule_changes[rule_name] = {"consumed": [], "produced": [], "degraded": []}

                if change["type"] == "consumed":
                    rule_changes[rule_name]["consumed"].append(change)
                elif change["type"] == "produced":
                    rule_changes[rule_name]["produced"].append(change)
                elif change["type"] == "degraded":
                    rule_changes[rule_name]["degraded"].append(change)

            # Display events in order: degradation first, then biological processes
            event_count = 0

            # 1. DEGRADATION EVENTS (always show first)
            for rule_name, rule_change in rule_changes.items():
                if rule_name == "Natural degradation" and rule_change["degraded"]:
                    event_count += 1
                    log_entries.append("")
                    log_entries.append(f"    [{event_count}] Natural Degradation")

                    # NEW: Show interferon influence if active
                    if self.interferon_level > 0:
                        log_entries.append(f"        (Enhanced by interferon: {self.interferon_level:.1f}/100)")

                    # Enhanced formatting for multiple degraded entities
                    degraded_items = []
                    for deg_change in rule_change["degraded"]:
                        entity_name = deg_change["entity"]
                        count = deg_change["count"]
                        degraded_items.append(f"{count} {self._format_entity_name(entity_name)}")

                    if len(degraded_items) == 1:
                        log_entries.append(f"        - {degraded_items[0]} degraded")
                    else:
                        log_entries.append("        Degraded:")
                        for item in degraded_items:
                            log_entries.append(f"          - {item}")

            # 2. BIOLOGICAL PROCESSES (transitions, productions) - ENHANCED FOR MULTIPLE ENTITIES
            for rule_name, rule_change in rule_changes.items():
                if rule_name == "Natural degradation":
                    continue  # Already handled above

                consumed = rule_change["consumed"]
                produced = rule_change["produced"]

                if consumed or produced:
                    event_count += 1
                    log_entries.append("")
                    log_entries.append(f"    [{event_count}] {rule_name}")

                    # Enhanced display for multiple consumed entities
                    if consumed:
                        consumed_items = []
                        for cons_change in consumed:
                            entity_name = cons_change["entity"]
                            count = cons_change["count"]
                            consumed_items.append(f"{count} {self._format_entity_name(entity_name)}")

                        if len(consumed_items) == 1:
                            log_entries.append(f"        Consumed: {consumed_items[0]}")
                        else:
                            log_entries.append("        Consumed:")
                            for item in consumed_items:
                                log_entries.append(f"          - {item}")

                    # Enhanced display for multiple produced entities
                    if produced:
                        produced_items = []
                        for prod_change in produced:
                            entity_name = prod_change["entity"]
                            count = prod_change["count"]
                            produced_items.append(f"{count} {self._format_entity_name(entity_name)}")

                        if len(produced_items) == 1:
                            log_entries.append(f"        Produced: {produced_items[0]}")
                        else:
                            log_entries.append("        Produced:")
                            for item in produced_items:
                                log_entries.append(f"          + {item}")

                    # NEW: Show interferon generation if this rule added interferon
                    # Interferon generation (consuming or catalytic)
                    rule_def = next((r for r in self.transition_rules if r.get("name") == rule_name), None)
                    if rule_def:
                        rule_interferon = float(rule_def.get("interferon_amount", 0.0) or 0.0)
                        if rule_interferon > 0:
                            mini_changes = []
                            if consumed: mini_changes.extend(consumed)
                            if produced: mini_changes.extend(produced)
                            applications = self._estimate_applications_from_changes(rule_def, mini_changes)
                            interferon_from_rule = applications * rule_interferon
                            if interferon_from_rule > 0:
                                log_entries.append(f"        Interferon generated: +{interferon_from_rule:.1f}")

            if event_count == 0:
                log_entries.append("")
                log_entries.append("    No events occurred this turn")

        else:
            log_entries.append("")
            log_entries.append("  Events this turn:")
            log_entries.append("    No events occurred this turn")

        # FINAL POPULATION - Show results WITH LOCATION GROUPING
        log_entries.append("")
        log_entries.append("  Population at end:")
        if self.entities:
            total_entities = sum(self.entities.values())

            # Add location-grouped display
            location_sections = self._generate_location_grouped_population()
            for section in location_sections:
                log_entries.extend(section)

            log_entries.append("")
            log_entries.append(f"    Total entities: {total_entities}")
        else:
            log_entries.append("    *** No entities remaining - EXTINCTION ***")

        # NEW: Add interferon status at the end of each turn
        log_entries.append("")
        log_entries.append(f"  Interferon activity is at {self.interferon_level:.1f}/100")

        return log_entries

    def _generate_location_grouped_population(self):
        """Generate location-grouped population display for console log"""
        if not self.entities:
            return []

        # Group entities by location
        entities_by_location = self._group_entities_by_location()

        # Define location display order
        location_order = ["extracellular", "membrane", "endosome", "cytoplasm", "nucleus"]
        location_labels = {
            "extracellular": "EXTRACELLULAR",
            "membrane": "MEMBRANE",
            "cytoplasm": "CYTOPLASM",
            "endosome": "ENDOSOME",
            "nucleus": "NUCLEUS"
        }

        sections = []

        # Display entities by location in order
        for location in location_order:
            if location in entities_by_location:
                section = self._format_location_section_for_log(
                    location,
                    entities_by_location[location],
                    location_labels.get(location, location.upper())
                )
                sections.append(section)
                del entities_by_location[location]  # Remove from dict to track displayed

        # Display any remaining locations not in the standard order
        for location, location_entities in entities_by_location.items():
            section = self._format_location_section_for_log(
                location,
                location_entities,
                location.upper()
            )
            sections.append(section)

        return sections

    def _group_entities_by_location(self):
        """Group entities by their location property"""
        entities_by_location = {}

        for entity_name, count in self.entities.items():
            # Get location from database if available
            location = "unknown"
            if self.db_manager:
                entity_data = self.db_manager.get_entity(entity_name)
                if entity_data:
                    location = entity_data.get("location", "unknown")

            if location not in entities_by_location:
                entities_by_location[location] = []
            entities_by_location[location].append((entity_name, count))

        return entities_by_location

    def _format_location_section_for_log(self, location, location_entities, label):
        """Format a location section for the console log"""
        # Sort entities alphabetically by name
        location_entities.sort(key=lambda x: x[0].lower())

        section = []
        section.append(f"    [{label}]")

        # Entities in this location
        for entity_name, count in location_entities:
            formatted_name = self._format_entity_name(entity_name)
            section.append(f"      {count:3d}x {formatted_name}")

        return section

    def _format_entity_name(self, entity_name):
        """Format entity names for better readability"""
        # Remove redundant parenthetical location info if it makes the name too long
        if len(entity_name) > 45:
            # Try to shorten common patterns
            if "(extracellular)" in entity_name:
                return entity_name.replace("(extracellular)", "(ext)")
            elif "(cytoplasm)" in entity_name:
                return entity_name.replace("(cytoplasm)", "(cyto)")
            elif "(endosome)" in entity_name:
                return entity_name.replace("(endosome)", "(endo)")
            elif "(nucleus)" in entity_name:
                return entity_name.replace("(nucleus)", "(nuc)")

        return entity_name

    def is_simulation_over(self):
        """Check if simulation should end"""
        return len(self.entities) == 0

    def get_interferon_level(self):
        """Get current interferon level (for UI display)"""
        return self.interferon_level


class GameModule(ABC):
    """Abstract base class for all game modules"""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.frame = ttk.Frame(parent)
        self.setup_ui()

    @abstractmethod
    def setup_ui(self):
        """Setup the UI for this module"""
        pass

    def show(self):
        """Show this module"""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this module"""
        self.frame.pack_forget()

    def destroy(self):
        """Clean up this module"""
        self.frame.destroy()


class MenuModule(GameModule):
    """Main menu module"""

    def setup_ui(self):
        # Title
        title_label = ttk.Label(
            self.frame,
            text="Virus Sandbox",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=50)

        # Subtitle
        subtitle_label = ttk.Label(
            self.frame,
            text="Create and simulate your own virtual viruses",
            font=("Arial", 12, "italic")
        )
        subtitle_label.pack(pady=(0, 50))

        # Menu buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack()

        # Start new game button
        start_btn = ttk.Button(
            button_frame,
            text="Start New Game",
            command=self.start_new_game,
            width=20
        )
        start_btn.pack(pady=10)

        # Continue game button (placeholder)
        continue_btn = ttk.Button(
            button_frame,
            text="Continue Game",
            command=self.continue_game,
            width=20,
            state='disabled'  # Disabled for now
        )
        continue_btn.pack(pady=5)

        # Sample database button in menu
        sample_btn = ttk.Button(
            button_frame,
            text="Create Sample Database",
            command=self.create_sample_database,
            width=20
        )
        sample_btn.pack(pady=5)

        # Enter editor button
        editor_btn = ttk.Button(
            button_frame,
            text="Gene Database Editor",
            command=self.open_editor,
            width=20
        )
        editor_btn.pack(pady=5)

        # Exit button
        exit_btn = ttk.Button(
            button_frame,
            text="Exit",
            command=self.controller.quit_application,
            width=20
        )
        exit_btn.pack(pady=10)

    def start_new_game(self):
        """Start a new game - first select database, then go to builder"""
        file_path = filedialog.askopenfilename(
            title="Select Gene Database",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )

        if file_path:
            try:
                # Try to load the database
                db_manager = GeneDatabaseManager()
                db_manager.load_database(file_path)

                # Pass the database to the controller
                self.controller.start_new_game_with_database(db_manager)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load database:\n{e}")

    def continue_game(self):
        """Continue existing game - placeholder"""
        messagebox.showinfo("Not Implemented", "Continue game functionality will be added later")

    def create_sample_database(self):
        """Create and save a sample database"""
        file_path = filedialog.asksaveasfilename(
            title="Save Sample Database As",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json",
            initialdir=os.getcwd(),
            initialvalue="sample_virus_genes.json"
        )

        if file_path:
            try:
                db_manager = GeneDatabaseManager()
                db_manager.create_sample_database()
                db_manager.save_database(file_path)
                messagebox.showinfo("Success", f"Sample database created: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create sample database:\n{e}")

    def open_editor(self):
        """Open gene editor"""
        self.controller.switch_to_module("editor")


class BuilderModule(GameModule):
    """Virus builder module - UPDATED WITH IMPROVED LAYOUT, GENE DETAILS, ROUNDS COUNTER, SKIP ROUND BUTTON, AND POLYMERASE GENE LIMITING"""

    BIG_BUDGET = 1_000_000  # neutralize legacy budget checks in VirusBuilder

    def __init__(self, parent, controller):
        self.db_manager = None
        self.game_state = None
        self.gene_db = None
        self.virus_builder = None
        self.current_display_mode = "virus"  # "virus" or "gene"
        self.current_selected_gene = None
        super().__init__(parent, controller)

    # --- wiring ---
    def set_game_state(self, game_state):
        """Give the builder access to EP + deck; keep editor logic untouched."""
        self.game_state = game_state
        # Mirror to a very large budget so legacy budget checks never block
        if self.virus_builder:
            self.virus_builder.budget = self.BIG_BUDGET
            self.virus_builder.set_game_state(game_state)  # Wire game state to virus builder
        self.update_virus_display()
        self.update_starter_dropdown()  # Update starter options

    def set_database_manager(self, db_manager):
        """Called by the controller when a DB is loaded."""
        self.db_manager = db_manager
        self.gene_db = GeneDatabase(db_manager)
        self.virus_builder = VirusBuilder(self.gene_db, self.game_state)  # Pass game state

        # Neutralize internal budget checks
        self.virus_builder.budget = self.BIG_BUDGET

        self.update_gene_list()
        self.update_virus_display()
        self.update_starter_dropdown()  # Update starter options

    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(header_frame, text="Virus Builder", font=("Arial", 16, "bold")).pack(side=tk.LEFT)

        # Main content area - UPDATED LAYOUT
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top section - Gene lists (reduced height)
        gene_lists_frame = ttk.Frame(main_frame)
        gene_lists_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        # Left panel - Available genes
        available_frame = ttk.LabelFrame(gene_lists_frame, text="Available Genes (from your Deck)", padding=10)
        available_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Search/filter
        search_frame = ttk.Frame(available_frame)
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.update_gene_list())

        # Gene list - REDUCED HEIGHT
        self.available_genes_list = tk.Listbox(available_frame, selectmode=tk.SINGLE, height=8)
        self.available_genes_list.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        # Add click handler for gene details
        self.available_genes_list.bind('<<ListboxSelect>>', self.on_available_gene_select)
        self.available_genes_list.bind('<Button-1>', self.on_available_gene_click)

        # Add button
        ttk.Button(available_frame, text="Add Selected Gene", command=self.add_gene).pack(fill=tk.X)

        # Right panel - Selected genes and controls
        selected_frame = ttk.LabelFrame(gene_lists_frame, text="Selected Genes", padding=10)
        selected_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Selected genes list - REDUCED HEIGHT
        self.selected_genes_list = tk.Listbox(selected_frame, selectmode=tk.SINGLE, height=8)
        self.selected_genes_list.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        # Add click handler for gene details
        self.selected_genes_list.bind('<<ListboxSelect>>', self.on_selected_gene_select)
        self.selected_genes_list.bind('<Button-1>', self.on_selected_gene_click)

        # Remove button
        button_row = ttk.Frame(selected_frame)
        button_row.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(button_row, text="Remove Selected Gene", command=self.remove_gene).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5)
        )

        # MOVED: Starter entity selection and controls
        controls_frame = ttk.LabelFrame(selected_frame, text="Simulation Controls", padding=10)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Starter entity selection
        starter_row = ttk.Frame(controls_frame)
        starter_row.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(starter_row, text="Starting Entity:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.starter_var = tk.StringVar()
        self.starter_dropdown = ttk.Combobox(starter_row, textvariable=self.starter_var,
                                             width=25, state="readonly")
        self.starter_dropdown.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        self.starter_dropdown.bind('<<ComboboxSelected>>', self.on_starter_selection_changed)

        # Validation indicator
        self.starter_status_label = ttk.Label(starter_row, text="", font=("Arial", 9), foreground="red")
        self.starter_status_label.pack(side=tk.LEFT, padx=(5, 0))

        # Rounds remaining counter
        rounds_row = ttk.Frame(controls_frame)
        rounds_row.pack(fill=tk.X, pady=(0, 10))

        self.rounds_label = ttk.Label(rounds_row, text="Rounds Remaining: --/--",
                                      font=("Arial", 11, "bold"), foreground="#dc2626")
        self.rounds_label.pack(side=tk.LEFT)

        # Help text for rounds
        rounds_help = ttk.Label(rounds_row, text="(Build → Play cycles)",
                                font=("Arial", 9, "italic"), foreground="gray")
        rounds_help.pack(side=tk.LEFT, padx=(10, 0))

        # EP + Skip Round + Start Simulation - UPDATED WITH SKIP ROUND BUTTON
        sim_row = ttk.Frame(controls_frame)
        sim_row.pack(fill=tk.X)
        self.ep_label = ttk.Label(sim_row, text="EP: 0", font=("Arial", 11, "bold"))
        self.ep_label.pack(side=tk.LEFT)

        # Skip Round button (on the left side)
        self.skip_round_button = ttk.Button(
            sim_row,
            text="Skip Round",
            command=self.skip_round
        )
        self.skip_round_button.pack(side=tk.RIGHT, padx=(0, 5))

        self.start_sim_button = ttk.Button(
            sim_row,
            text="Start Simulation",
            command=self.start_simulation
        )
        self.start_sim_button.pack(side=tk.RIGHT)

        # Bottom section - ENLARGED Properties/Details panel
        details_frame = ttk.LabelFrame(main_frame, text="Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)

        # Control buttons for details panel
        details_controls = ttk.Frame(details_frame)
        details_controls.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(details_controls, text="View:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        ttk.Button(details_controls, text="Show Virus Properties",
                   command=self.show_virus_properties).pack(side=tk.LEFT, padx=(10, 5))

        # Status indicator
        self.details_status_label = ttk.Label(details_controls, text="Showing: Virus Properties",
                                              font=("Arial", 9, "italic"), foreground="blue")
        self.details_status_label.pack(side=tk.LEFT, padx=(10, 0))

        # ENLARGED text area for properties/details
        self.details_text = tk.Text(details_frame, state='disabled', wrap=tk.WORD, height=15)

        # Add scrollbar to text area
        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.details_text = tk.Text(text_frame, state='disabled', wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.config(yscrollcommand=scrollbar.set)

        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def show(self):
        super().show()
        self.update_gene_list()
        self.update_virus_display()
        self.update_starter_dropdown()  # Update starter options when showing
        if self.virus_builder:
            self.virus_builder.budget = self.BIG_BUDGET

    # --------- Gene selection handlers for details display ---------

    def on_available_gene_select(self, event):
        """Handle selection in available genes list"""
        selection = self.available_genes_list.curselection()
        if not selection:
            return
        self.handle_gene_selection_from_available(selection[0])

    def on_available_gene_click(self, event):
        """Handle click in available genes list"""
        self.available_genes_list.after(10, self.handle_available_gene_click)

    def handle_available_gene_click(self):
        """Handle available gene click with delay"""
        selection = self.available_genes_list.curselection()
        if selection:
            self.handle_gene_selection_from_available(selection[0])

    def handle_gene_selection_from_available(self, index):
        """Handle gene selection from available genes list"""
        try:
            display = self.available_genes_list.get(index)
            gene_name = display.rsplit(" (", 1)[0]
            self.show_gene_details(gene_name)
            # Clear selection in other list
            self.selected_genes_list.selection_clear(0, tk.END)
        except (tk.TclError, IndexError):
            pass

    def on_selected_gene_select(self, event):
        """Handle selection in selected genes list"""
        selection = self.selected_genes_list.curselection()
        if not selection:
            return
        self.handle_gene_selection_from_selected(selection[0])

    def on_selected_gene_click(self, event):
        """Handle click in selected genes list"""
        self.selected_genes_list.after(10, self.handle_selected_gene_click)

    def handle_selected_gene_click(self):
        """Handle selected gene click with delay"""
        selection = self.selected_genes_list.curselection()
        if selection:
            self.handle_gene_selection_from_selected(selection[0])

    def handle_gene_selection_from_selected(self, index):
        """Handle gene selection from selected genes list"""
        try:
            gene_name = self.selected_genes_list.get(index)
            self.show_gene_details(gene_name)
            # Clear selection in other list
            self.available_genes_list.selection_clear(0, tk.END)
        except (tk.TclError, IndexError):
            pass

    def show_gene_details(self, gene_name):
        """Show details for a specific gene"""
        if not self.db_manager:
            return

        gene = self.db_manager.get_gene(gene_name)
        if not gene:
            return

        self.current_display_mode = "gene"
        self.current_selected_gene = gene_name
        self.details_status_label.config(text=f"Showing: {gene_name}")

        # Build gene details text
        details_text = self.format_gene_details(gene)

        # Update text area
        self.details_text.config(state='normal')
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details_text)
        self.details_text.config(state='disabled')

    def show_virus_properties(self):
        """Show virus properties (default view)"""
        self.current_display_mode = "virus"
        self.current_selected_gene = None
        self.details_status_label.config(text="Showing: Virus Properties")

        # Clear selections in both lists
        self.available_genes_list.selection_clear(0, tk.END)
        self.selected_genes_list.selection_clear(0, tk.END)

        self.update_virus_display()

    def format_gene_details(self, gene):
        """Format gene details for display"""
        details = []

        # Basic info
        details.append(f"Gene: {gene['name']}")
        details.append(f"Cost: {gene.get('cost', 0)} EP")

        # NEW: Show polymerase status
        if gene.get('is_polymerase', False):
            details.append("Type: POLYMERASE GENE")

        details.append("")

        # Description
        description = gene.get('description', 'No description available')
        details.append("Description:")
        details.append(f"  {description}")
        details.append("")

        # Prerequisites
        prereqs = gene.get('requires', [])
        if prereqs:
            details.append("Prerequisites:")
            for req in prereqs:
                details.append(f"  • {req}")
            details.append("")

        # Effects
        effects = gene.get('effects', [])
        if effects:
            details.append("Effects:")
            for i, effect in enumerate(effects, 1):
                effect_desc = self.format_effect_for_details(effect)
                details.append(f"  {i}. {effect_desc}")
                details.append("")
        else:
            details.append("Effects: None")
            details.append("")

        return "\n".join(details)

    def format_effect_for_details(self, effect):
        """Format a single effect for detailed display - UPDATED FOR MULTIPLE INPUTS/OUTPUTS"""
        effect_type = effect.get("type", "unknown")

        if effect_type == "add_transition":
            rule = effect.get("rule", {})
            rule_name = rule.get("name", "Unknown")
            probability = rule.get("probability", 0) * 100
            rule_type = rule.get("rule_type", "per_entity")

            # Format inputs and outputs
            inputs = rule.get("inputs", [])
            outputs = rule.get("outputs", [])

            # Format inputs with better multi-entity display
            input_desc = []
            consumed_status = None
            for inp in inputs:
                consumed = inp.get("consumed", True)
                if consumed_status is None:
                    consumed_status = consumed
                input_desc.append(f"{inp['count']}x {inp['entity']}")

            # Add consumed/not consumed note (applies to all inputs)
            consumed_note = " (all consumed)" if consumed_status else " (not consumed)"
            if input_desc and consumed_status is not None:
                input_desc[-1] += consumed_note

            # Format outputs
            output_desc = []
            for out in outputs:
                output_desc.append(f"{out['count']}x {out['entity']}")

            # Build display with improved multi-entity formatting
            details = [f"Transition: {rule_name}"]
            details.append(f"  Probability: {probability:.1f}% {rule_type}")

            # Format inputs section
            if input_desc:
                if len(input_desc) == 1:
                    details.append(f"  Input: {input_desc[0]}")
                else:
                    details.append(f"  Inputs:")
                    for inp in input_desc:
                        details.append(f"    - {inp}")
            else:
                details.append(f"  Inputs: None")

            # Format outputs section
            if output_desc:
                if len(output_desc) == 1:
                    details.append(f"  Output: {output_desc[0]}")
                else:
                    details.append(f"  Outputs:")
                    for out in output_desc:
                        details.append(f"    - {out}")
            else:
                details.append(f"  Outputs: None")

            # Show interferon if present
            interferon_amount = float(rule.get("interferon_amount", 0) or 0)
            if interferon_amount:
                details.append(f"  Interferon: +{interferon_amount:.2f} per application")

            return "\n".join(details)

        elif effect_type == "modify_transition":
            rule_name = effect.get("rule_name", "Unknown")
            modification = effect.get("modification", {})
            multiplier = modification.get("probability_multiplier", 1.0)

            return f"Modify Transition: {rule_name}\n  Probability multiplier: {multiplier}x"

        else:
            return f"Unknown effect type: {effect_type}"

    # --------- Starter entity management ---------

    def update_starter_dropdown(self):
        """Update the starter entity dropdown with available options"""
        if not self.game_state or not self.db_manager:
            self.starter_dropdown['values'] = []
            self.starter_var.set("")
            self.starter_status_label.config(text="No database loaded", foreground="red")
            return

        # Get available starter entities
        available_starters = self.game_state.get_available_starter_entities()

        if not available_starters:
            self.starter_dropdown['values'] = []
            self.starter_var.set("")
            self.starter_status_label.config(text="No starter entities defined", foreground="red")
            return

        # Populate dropdown
        self.starter_dropdown['values'] = available_starters

        # Set current selection
        current_starter = self.game_state.get_selected_starter_entity()
        if current_starter in available_starters:
            self.starter_var.set(current_starter)
            self.starter_status_label.config(text="✓", foreground="green")
        else:
            # Auto-select first available
            self.game_state.set_starter_entity(available_starters[0])
            self.starter_var.set(available_starters[0])
            self.starter_status_label.config(text="✓", foreground="green")

    def on_starter_selection_changed(self, event=None):
        """Handle starter entity selection change"""
        if not self.game_state:
            return

        selected_entity = self.starter_var.get()
        if self.game_state.set_starter_entity(selected_entity):
            self.starter_status_label.config(text="✓", foreground="green")
            # Update virus capabilities display to reflect new starter
            if self.current_display_mode == "virus":
                self.update_virus_display()
        else:
            self.starter_status_label.config(text="Invalid selection", foreground="red")

    def validate_starter_selection(self) -> tuple[bool, str]:
        """Validate current starter selection before simulation"""
        if not self.game_state:
            return False, "No game state"

        return self.game_state.validate_starter_entity()

    # --------- Rounds counter management ---------

    def update_rounds_display(self):
        """Update the rounds remaining display and button states"""
        if not self.game_state:
            self.rounds_label.config(text="Rounds Remaining: --/--", foreground="gray")
            self.start_sim_button.config(state='disabled', text="Start Simulation")
            self.skip_round_button.config(state='disabled')  # Disable skip button too
            return

        cycles_used = self.game_state.cycles_used
        cycle_limit = self.game_state.cycle_limit
        remaining = cycle_limit - cycles_used

        # Update text and color based on remaining rounds
        if remaining <= 0:
            self.rounds_label.config(text=f"Rounds Remaining: 0/{cycle_limit}", foreground="#dc2626")
            # Disable both buttons if no rounds left
            self.start_sim_button.config(state='disabled', text="No Rounds Left")
            self.skip_round_button.config(state='disabled')  # Disable skip button too
        elif remaining <= 2:
            self.rounds_label.config(text=f"Rounds Remaining: {remaining}/{cycle_limit}", foreground="#dc2626")  # Red
            self.start_sim_button.config(state='normal', text="Start Simulation")
            self.skip_round_button.config(state='normal')  # Enable skip button
        elif remaining <= 5:
            self.rounds_label.config(text=f"Rounds Remaining: {remaining}/{cycle_limit}",
                                     foreground="#ea580c")  # Orange
            self.start_sim_button.config(state='normal', text="Start Simulation")
            self.skip_round_button.config(state='normal')  # Enable skip button
        else:
            self.rounds_label.config(text=f"Rounds Remaining: {remaining}/{cycle_limit}", foreground="#16a34a")  # Green
            self.start_sim_button.config(state='normal', text="Start Simulation")
            self.skip_round_button.config(state='normal')  # Enable skip button

    def update_virus_display(self):
        """Refresh selected genes, capabilities, EP label, and rounds counter."""
        # Selected genes list
        self.selected_genes_list.delete(0, tk.END)
        if self.virus_builder:
            for gene in self.virus_builder.selected_genes:
                # VirusBuilder stores dicts like {"name": "..."} in many versions
                self.selected_genes_list.insert(tk.END, gene["name"] if isinstance(gene, dict) else str(gene))

        # Update details display based on current mode
        if self.current_display_mode == "virus":
            self.update_virus_capabilities_display()
        elif self.current_display_mode == "gene" and self.current_selected_gene:
            # Refresh gene details in case something changed
            self.show_gene_details(self.current_selected_gene)

        # EP label (single counter) - UPDATED TO SHOW STARTING ENTITY BONUS
        current_ep = self.game_state.ep if self.game_state else 0
        if self.game_state:
            starting_count = self.game_state.get_starting_entity_count()
            if starting_count > 10:
                bonus = starting_count - 10
                self.ep_label.config(text=f"EP: {current_ep} | Start: {starting_count} (+{bonus})")
            else:
                self.ep_label.config(text=f"EP: {current_ep}")
        else:
            self.ep_label.config(text=f"EP: {current_ep}")

        # Update rounds counter and button states
        self.update_rounds_display()

    def update_virus_capabilities_display(self):
        """Update the virus capabilities display with enhanced transition info - UPDATED FOR MULTIPLE INPUTS/OUTPUTS"""
        # Get capabilities - UPDATED TO SHOW STARTER ENTITY
        caps = self.virus_builder.get_virus_capabilities() if self.virus_builder else {
            "starting_entities": {},
            "possible_entities": [],
            "transition_rules": []
        }

        self.details_text.config(state='normal')
        self.details_text.delete(1.0, tk.END)

        details = []

        # Show starting entities first
        if caps["starting_entities"]:
            details.append("=== STARTING ENTITIES ===")
            for entity, count in caps["starting_entities"].items():
                details.append(f"  {count}x {entity}")
            details.append("")

        # Show all possible entities
        if caps["possible_entities"]:
            details.append("=== ALL POSSIBLE ENTITIES ===")
            for entity in sorted(caps["possible_entities"]):
                details.append(f"  • {entity}")
            details.append("")

        # Show all transition rules in detail with improved multi-entity formatting
        if caps["transition_rules"]:
            details.append("=== VIRUS TRANSITIONS ===")
            for i, rule in enumerate(caps["transition_rules"], 1):
                rule_name = rule.get("name", f"Rule {i}")
                probability = rule.get("probability", 0) * 100
                rule_type = rule.get("rule_type", "per_entity")

                details.append(f"{i}. {rule_name}")
                details.append(f"   Probability: {probability:.1f}% {rule_type}")

                # Inputs with improved multi-entity formatting
                inputs = rule.get("inputs", [])
                if inputs:
                    if len(inputs) == 1:
                        inp = inputs[0]
                        consumed = " (consumed)" if inp.get("consumed", True) else " (not consumed)"
                        details.append(f"   Input: {inp['count']}x {inp['entity']}{consumed}")
                    else:
                        consumed_status = inputs[0].get("consumed", True) if inputs else True
                        consumed_note = " (all consumed)" if consumed_status else " (none consumed)"
                        details.append(f"   Inputs{consumed_note}:")
                        for inp in inputs:
                            details.append(f"     - {inp['count']}x {inp['entity']}")

                # Outputs with improved multi-entity formatting
                outputs = rule.get("outputs", [])
                if outputs:
                    if len(outputs) == 1:
                        out = outputs[0]
                        details.append(f"   Output: {out['count']}x {out['entity']}")
                    else:
                        details.append(f"   Outputs:")
                        for out in outputs:
                            details.append(f"     - {out['count']}x {out['entity']}")

                interferon_amount = float(rule.get("interferon_amount", 0) or 0)
                if interferon_amount:
                    details.append(f"   Interferon: +{interferon_amount:.2f} per application")

                details.append("")
        else:
            details.append("=== VIRUS TRANSITIONS ===")
            details.append("No special transitions defined.")
            details.append("(Only natural degradation will occur)")
            details.append("")

        # Show selected genes - UPDATED TO SHOW POLYMERASE STATUS
        if self.virus_builder and self.virus_builder.selected_genes:
            details.append("=== SELECTED GENES ===")
            for gene in self.virus_builder.selected_genes:
                gene_name = gene["name"] if isinstance(gene, dict) else str(gene)
                # NEW: Show polymerase indicator
                if gene.get("is_polymerase", False):
                    details.append(f"  • {gene_name} (POLYMERASE)")
                else:
                    details.append(f"  • {gene_name}")
        else:
            details.append("=== SELECTED GENES ===")
            details.append("No genes selected (basic virus only)")

        self.details_text.insert(1.0, "\n".join(details))
        self.details_text.config(state='disabled')

    # --------- Core interactions ---------

    def update_gene_list(self):
        """Populate Available Genes limited to the player's deck (plus filter)."""
        if not self.gene_db:
            return

        filter_text = (self.search_var.get() if hasattr(self, "search_var") else "").strip().lower()

        if self.game_state and self.game_state.deck:
            candidate_names = list(self.game_state.deck)
        else:
            candidate_names = []

        available = []
        for name in sorted(candidate_names):
            if filter_text and filter_text not in name.lower():
                continue
            gene = self.db_manager.get_gene(name) if self.db_manager else None
            if not gene:
                continue
            available.append(name)

        self.available_genes_list.delete(0, tk.END)
        for name in available:
            cost = 0
            if self.db_manager:
                g = self.db_manager.get_gene(name)
                if g:
                    cost = g.get("cost", 0)
            self.available_genes_list.insert(tk.END, f"{name} ({cost})")

    def add_gene(self):
        """Add the selected gene - UPDATED to validate before spending EP (polymerase-safe)"""
        if not self.virus_builder or not self.db_manager:
            return

        sel = self.available_genes_list.curselection()
        if not sel:
            messagebox.showinfo("Add Gene", "Please select a gene from your deck.")
            # Keep UI consistent
            self.update_virus_display()
            return

        display = self.available_genes_list.get(sel[0])
        gene_name = display.rsplit(" (", 1)[0]

        if not self.game_state:
            messagebox.showwarning("No Game State", "Game state not initialized.")
            self.update_virus_display()
            return

        if not self.game_state.can_install_gene_this_round():
            messagebox.showinfo("Install limit", "You can only install one gene per round.")
            self.update_virus_display()
            return

        # --- Validate with the builder FIRST (no state changes yet) ---
        ok, reason = self.virus_builder.can_add_gene(gene_name)

        # Helpful messages for known failure reasons (no EP spent yet)
        if not ok:
            if reason == "polymerase_limit":
                current_polymerase = self.virus_builder.get_selected_polymerase_gene()
                if current_polymerase:
                    messagebox.showerror(
                        "Polymerase Gene Limit",
                        "Only one polymerase gene can be installed at a time.\n\n"
                        f"Currently installed: {current_polymerase}\n"
                        f"Trying to add: {gene_name}\n\n"
                        "Remove the existing polymerase gene first if you want to use a different one."
                    )
                else:
                    messagebox.showerror("Cannot Add Gene",
                                         f"Unable to add '{gene_name}' due to polymerase limit.")
            elif reason == "already_installed":
                messagebox.showinfo("Already Installed",
                                    f"'{gene_name}' is already installed.")
            elif reason == "missing_prerequisites":
                messagebox.showerror("Missing Prerequisites",
                                     f"'{gene_name}' requires other genes first.")
            elif reason == "unknown_gene":
                messagebox.showerror("Unknown Gene",
                                     f"'{gene_name}' was not found.")
            else:
                # Fallback (e.g., builder budget guard—even though BIG_BUDGET neutralizes it)
                messagebox.showerror("Cannot Add Gene",
                                     f"Unable to add '{gene_name}'.")
            # Make sure EP label & lists stay in sync
            self.update_virus_display()
            return

        # --- Ask and check EP AFTER validation ---
        cost = self.game_state.get_gene_cost(gene_name)
        if not messagebox.askyesno("Confirm Purchase", f"Spend {cost} EP to add '{gene_name}'?"):
            self.update_virus_display()
            return

        if not self.game_state.can_afford_insert(gene_name):
            messagebox.showwarning("Not enough EP", f"You need {cost} EP for {gene_name}.")
            self.update_virus_display()
            return

        # Deduct EP now that we know the add should succeed
        if not self.game_state.spend_for_insert(gene_name):
            # Defensive: if something changed between can_afford and spend
            messagebox.showwarning("EP Error", "Could not spend EP for this gene.")
            self.update_virus_display()
            return

        # records gene installed this round
        self.game_state.record_gene_install()

        # Now actually add to the builder (should succeed since validated)
        success = self.virus_builder.add_gene(gene_name)
        if not success:
            # Extremely unlikely given the earlier can_add_gene check; don't leave EP deducted
            # If you later add a refund function, call it here. For now, surface a clear error.
            messagebox.showerror("Unexpected Error",
                                 f"Adding '{gene_name}' failed after EP was spent. "
                                 "Please remove the gene and try again.")
            # Still refresh the UI to avoid stale labels
            self.update_virus_display()
            return

        # Track installed genes in game state (deck-building record)
        if gene_name not in self.game_state.installed_genes:
            self.game_state.installed_genes.append(gene_name)

        # Keep builder budget neutralized and refresh UI
        self.virus_builder.budget = self.BIG_BUDGET
        self.update_virus_display()

    def remove_gene(self):
        """Remove the selected gene (CONFIRM, then spend EP, then remove)."""
        if not self.virus_builder:
            return

        sel = self.selected_genes_list.curselection()
        if not sel:
            messagebox.showinfo("Remove Gene", "Please select a gene to remove.")
            return

        gene_name = self.selected_genes_list.get(sel[0])

        if not self.game_state:
            messagebox.showwarning("No Game State", "Game state not initialized.")
            return

        cost = self.game_state.get_remove_cost(gene_name)

        # If they can't afford it, tell them and bail early
        if not self.game_state.can_afford_remove(gene_name):
            messagebox.showwarning(
                "Not enough EP",
                f"Removing '{gene_name}' costs {cost} EP, but you only have {self.game_state.ep} EP."
            )
            return

        # Confirm the spend
        if not messagebox.askyesno("Confirm Removal", f"Spend {cost} EP to remove '{gene_name}'?"):
            return


        # Spend EP first (one-way), then remove
        if not self.game_state.spend_for_remove(gene_name):
            messagebox.showwarning("EP Error", "Could not spend EP to remove this gene.")
            return

        self.virus_builder.remove_gene(gene_name)

        if gene_name in self.game_state.installed_genes:
            self.game_state.installed_genes.remove(gene_name)

        self.virus_builder.budget = self.BIG_BUDGET
        self.update_virus_display()

    def clear_all_genes(self):
        """Remove all selected genes; each removal costs EP. Stops if EP runs out."""
        if not self.virus_builder:
            return

        # Work on a copy because we'll mutate during iteration
        to_remove = [g["name"] if isinstance(g, dict) else str(g) for g in self.virus_builder.selected_genes]

        for gene_name in to_remove:
            cost = self.game_state.get_remove_cost(gene_name) if self.game_state else 0
            if not self.game_state or not self.game_state.can_afford_remove(gene_name):
                messagebox.showwarning("Not enough EP", f"Stopping. Need {cost} EP to remove '{gene_name}'.")
                break

            # Spend then remove
            if not self.game_state.spend_for_remove(gene_name):
                messagebox.showwarning("EP Error", f"Could not spend EP to remove '{gene_name}'.")
                break

            self.virus_builder.remove_gene(gene_name)
            if self.game_state and gene_name in self.game_state.installed_genes:
                self.game_state.installed_genes.remove(gene_name)

        if self.virus_builder:
            self.virus_builder.budget = self.BIG_BUDGET
        self.update_virus_display()

    # =================== SKIP ROUND FUNCTIONALITY ===================

    def skip_round(self):
        """Skip the current round without playing a simulation"""
        if not self.game_state:
            messagebox.showwarning("No Game State", "Game state not initialized.")
            return

        # Check if any rounds remaining
        if self.game_state.cycles_used >= self.game_state.cycle_limit:
            messagebox.showwarning("No Rounds Left",
                                   f"You have used all {self.game_state.cycle_limit} available rounds.\n"
                                   "This game session is complete.")
            return

        # Confirm the skip action
        remaining_rounds = self.game_state.cycle_limit - self.game_state.cycles_used
        if not messagebox.askyesno("Skip Round",
                                   f"Skip this round without playing a simulation?\n\n"
                                   f"This will consume 1 of your {remaining_rounds} remaining rounds, "
                                   f"but you'll still get a gene offer."):
            return

        # Call the controller's skip round method
        self.controller.skip_round()

    # =================== START SIMULATION ===================

    def start_simulation(self):
        """Build a blueprint and start Play - UPDATED WITH STARTER VALIDATION AND ROUNDS CHECK."""
        if not self.virus_builder:
            messagebox.showwarning("No Virus", "Please add genes to build your virus.")
            return

        # Check if any rounds remaining
        if self.game_state and self.game_state.cycles_used >= self.game_state.cycle_limit:
            messagebox.showwarning("No Rounds Left",
                                   f"You have used all {self.game_state.cycle_limit} available rounds.\n"
                                   "This game session is complete.")
            return

        # Validate starter entity selection
        is_valid, error_msg = self.validate_starter_selection()
        if not is_valid:
            messagebox.showerror("Invalid Starter Entity", f"Cannot start simulation:\n{error_msg}")
            return

        blueprint = self.virus_builder.get_virus_capabilities()

        # Ensure starting entities is not empty
        if not blueprint.get("starting_entities"):
            messagebox.showerror("No Starting Entities", "Virus blueprint has no starting entities defined.")
            return

        self.controller.start_simulation(blueprint)


class PlayModule(GameModule):
    """Virus simulation play module with dramatic turn display and location-based entity grouping - UPDATED WITH ENTITY TYPE BARS AND GENE DIALOG"""

    def __init__(self, parent, controller):
        self.simulation = None
        self.db_manager = None
        self.game_state = None
        self.game_won = False  # Track victory condition

        # NEW: Entity type tracking for bars
        self.entity_type_maxes = {"virion": 10, "RNA": 10, "DNA": 10, "protein": 10}  # Track max values for bars
        self.entity_type_current = {"virion": 0, "RNA": 0, "DNA": 0, "protein": 0}  # Current values

        super().__init__(parent, controller)

    # Wiring
    def set_game_state(self, game_state):
        self.game_state = game_state

    def set_database_manager(self, db_manager):
        self.db_manager = db_manager

    def setup_ui(self):
        # Header with improved styling
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=15, pady=10)

        title_label = ttk.Label(header_frame, text="Virus Simulation", font=("Arial", 18, "bold"))
        title_label.pack(side=tk.LEFT)

        # Back to builder button (more prominent)
        self.exit_btn = ttk.Button(
            header_frame,
            text="<-- Return to Builder",
            command=self.exit_to_builder,
            style="Accent.TButton"
        )
        self.exit_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Status bar with turn counter (more prominent)
        status_frame = ttk.Frame(self.frame, style="Card.TFrame")
        status_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Turn counter and interferon indicator in the same row
        status_info_frame = ttk.Frame(status_frame)
        status_info_frame.pack(pady=10)

        self.turn_label = ttk.Label(status_info_frame, text="Turn: 0", font=("Arial", 16, "bold"), foreground="#2563eb")
        self.turn_label.pack(side=tk.LEFT, padx=(0, 30))

        # Interferon level indicator
        self.interferon_label = ttk.Label(status_info_frame, text="Interferon: 0.0/100",
                                          font=("Arial", 14, "bold"), foreground="#dc2626")
        self.interferon_label.pack(side=tk.LEFT)

        # Main content area with improved layout
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        # Left panel - Simulation console (enhanced)
        console_frame = ttk.LabelFrame(main_frame, text="Simulation Log", padding=15)
        console_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            state='disabled',
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#f8fafc",
            fg="#1e293b"
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)

        # Right panel - Controls and stats (reorganized and enhanced)
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # === SIMULATION CONTROLS (Most Important Section) ===
        controls_frame = ttk.LabelFrame(right_panel, text="Simulation Controls", padding=15)
        controls_frame.pack(fill=tk.X, pady=(0, 15))

        # Primary action buttons (larger and more prominent)
        primary_buttons_frame = ttk.Frame(controls_frame)
        primary_buttons_frame.pack(fill=tk.X, pady=(0, 15))

        # Next Turn button (most prominent)
        self.next_turn_btn = ttk.Button(
            primary_buttons_frame,
            text="> Next Turn",
            command=self.next_turn,
            style="Accent.TButton"
        )
        self.next_turn_btn.pack(fill=tk.X, pady=(0, 8))

        # Multi-turn advancement buttons
        multi_turn_frame = ttk.LabelFrame(controls_frame, text="Fast Forward", padding=10)
        multi_turn_frame.pack(fill=tk.X, pady=(0, 15))

        # Row 1: 3 and 10 turns
        fast_row1 = ttk.Frame(multi_turn_frame)
        fast_row1.pack(fill=tk.X, pady=(0, 5))

        self.advance_3_btn = ttk.Button(
            fast_row1,
            text=">> +3 Turns",
            command=lambda: self.advance_multiple_turns(3),
            width=12
        )
        self.advance_3_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        self.advance_10_btn = ttk.Button(
            fast_row1,
            text=">> +10 Turns",
            command=lambda: self.advance_multiple_turns(10),
            width=12
        )
        self.advance_10_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Warning label for multi-turn
        warning_label = ttk.Label(
            multi_turn_frame,
            text="Warning: Multi-turn advancement cannot be undone",
            font=("Arial", 8),
            foreground="#dc2626"
        )
        warning_label.pack(pady=(5, 0))

        # === NEW: ENTITY TYPE BARS SECTION ===
        bars_frame = ttk.LabelFrame(right_panel, text="Entity Populations", padding=15)
        bars_frame.pack(fill=tk.X, pady=(0, 15))

        # Create bars for each entity type
        self.entity_bars = {}
        self.entity_labels = {}

        bar_configs = [
            ("virion", "Virions", "#6b7280"),  # Grey
            ("RNA", "RNA", "#22c55e"),  # Green
            ("DNA", "DNA", "#3b82f6"),  # Blue
            ("protein", "Proteins", "#f97316")  # Orange
        ]

        for i, (entity_type, display_name, color) in enumerate(bar_configs):
            # Label with count
            label_frame = ttk.Frame(bars_frame)
            label_frame.pack(fill=tk.X, pady=(0, 2))

            self.entity_labels[entity_type] = ttk.Label(
                label_frame,
                text=f"{display_name}: 0",
                font=("Arial", 10, "bold")
            )
            self.entity_labels[entity_type].pack(side=tk.LEFT)

            # Progress bar
            bar_frame = ttk.Frame(bars_frame)
            bar_frame.pack(fill=tk.X, pady=(0, 8))

            # Create a canvas for custom colored bar
            canvas = tk.Canvas(bar_frame, height=20, bg="#f1f5f9", relief=tk.FLAT, borderwidth=1)
            canvas.pack(fill=tk.X)

            self.entity_bars[entity_type] = {
                'canvas': canvas,
                'color': color,
                'display_name': display_name
            }

        # === NEW: GENES DIALOG BUTTON ===
        genes_frame = ttk.LabelFrame(right_panel, text="Virus Configuration", padding=15)
        genes_frame.pack(fill=tk.X, pady=(0, 15))

        self.show_genes_btn = ttk.Button(
            genes_frame,
            text="Show Installed Genes",
            command=self.show_genes_dialog
        )
        self.show_genes_btn.pack(fill=tk.X)

        # Configure custom styles
        self.setup_styles()

    def setup_styles(self):
        """Setup custom styles for enhanced appearance"""
        style = ttk.Style()

        # Accent button style for primary actions
        style.configure(
            "Accent.TButton",
            font=("Arial", 11, "bold"),
            padding=(10, 8)
        )

        # Card frame style for status
        style.configure(
            "Card.TFrame",
            relief="solid",
            borderwidth=1
        )

    def reset_entity_type_maxes(self):
        """Reset the maximum values for entity type bars when returning to builder"""
        self.entity_type_maxes = {"virion": 10, "RNA": 10, "DNA": 10, "protein": 10}
        self.entity_type_current = {"virion": 0, "RNA": 0, "DNA": 0, "protein": 0}

    def update_entity_type_bars(self, entities):
        """Update the entity type progress bars with current entity counts"""
        if not self.db_manager:
            return

        # Count entities by type
        type_counts = {"virion": 0, "RNA": 0, "DNA": 0, "protein": 0}

        for entity_name, count in entities.items():
            entity_data = self.db_manager.get_entity(entity_name)
            if entity_data:
                entity_class = entity_data.get("entity_class", "unknown")
                if entity_class in type_counts:
                    type_counts[entity_class] += count

        # Update maximums if any count exceeded current max
        overall_max_changed = False
        for entity_type, count in type_counts.items():
            if count > self.entity_type_maxes[entity_type]:
                self.entity_type_maxes[entity_type] = count
                overall_max_changed = True

        # If any max changed, update all maxes to the highest value for consistent scaling
        if overall_max_changed:
            new_overall_max = max(self.entity_type_maxes.values())
            for entity_type in self.entity_type_maxes:
                self.entity_type_maxes[entity_type] = max(new_overall_max, 10)  # Minimum of 10

        # Store current counts
        self.entity_type_current = type_counts.copy()

        # Update the visual bars
        overall_max = max(self.entity_type_maxes.values())

        for entity_type, bar_info in self.entity_bars.items():
            current_count = type_counts[entity_type]
            canvas = bar_info['canvas']
            color = bar_info['color']
            display_name = bar_info['display_name']

            # Update label
            self.entity_labels[entity_type].config(text=f"{display_name}: {current_count}")

            # Clear canvas
            canvas.delete("all")

            # Get canvas dimensions
            canvas.update_idletasks()
            width = canvas.winfo_width()
            height = canvas.winfo_height()

            if width > 1:  # Only draw if canvas is properly sized
                # Calculate bar width as percentage of max
                if overall_max > 0:
                    bar_width = (current_count / overall_max) * width
                else:
                    bar_width = 0

                # Draw background
                canvas.create_rectangle(0, 0, width, height, fill="#f1f5f9", outline="#e2e8f0")

                # Draw filled bar
                if bar_width > 0:
                    canvas.create_rectangle(2, 2, bar_width - 2, height - 2, fill=color, outline="")

                # Draw text overlay with count
                if current_count > 0:
                    fill_ratio = (current_count / overall_max) if overall_max else 0
                    text_color = "white" if fill_ratio >= 0.5 else "#374151"

                    canvas.create_text(width // 2, height // 2, text=str(current_count),
                                       fill=text_color, font=("Arial", 9, "bold"))

    def show_genes_dialog(self):
        """Show dialog with installed genes for this simulation"""
        if not hasattr(self, 'virus_blueprint'):
            messagebox.showinfo("No Genes", "No virus configuration available.")
            return

        genes = self.virus_blueprint.get("genes", [])
        if not genes:
            messagebox.showinfo("No Genes", "This virus has no installed genes (basic capsid only).")
            return

        # Create dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("Installed Genes")
        dialog.geometry("500x400")
        dialog.transient(self.frame)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (250)
        y = (dialog.winfo_screenheight() // 2) - (200)
        dialog.geometry(f"500x400+{x}+{y}")

        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(header_frame, text="Installed Genes", font=("Arial", 14, "bold")).pack()
        ttk.Label(header_frame, text=f"This virus has {len(genes)} installed genes:",
                  font=("Arial", 11)).pack(pady=(10, 0))

        # Gene list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Create listbox with scrollbar
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        gene_listbox = tk.Listbox(listbox_frame, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=gene_listbox.yview)
        gene_listbox.config(yscrollcommand=scrollbar.set)

        gene_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate with gene details
        for gene_name in genes:
            if self.db_manager:
                gene_data = self.db_manager.get_gene(gene_name)
                if gene_data:
                    cost = gene_data.get('cost', 0)
                    is_polymerase = gene_data.get('is_polymerase', False)

                    if is_polymerase:
                        display_text = f"{gene_name} ({cost} EP, Polymerase)"
                    else:
                        display_text = f"{gene_name} ({cost} EP)"

                    gene_listbox.insert(tk.END, display_text)
                else:
                    gene_listbox.insert(tk.END, f"{gene_name} (Unknown gene)")
            else:
                gene_listbox.insert(tk.END, gene_name)

        # Close button
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack()

        # Auto-focus and handle escape key
        dialog.focus_set()
        dialog.bind('<Escape>', lambda e: dialog.destroy())

    # Update the existing update_entities_display method to use the new bars
    def update_entities_display(self, entities):
        """Update entity display using the new type bars instead of location grouping"""
        # Update the new entity type bars
        self.update_entity_type_bars(entities)

    def exit_to_builder(self):
        """Mark offer pending, check milestone achievements, reset entity bars, and return to Builder"""
        # Prevent returning to builder if game was won
        if self.game_won:
            messagebox.showinfo("Game Complete",
                                "This simulation session is complete! You achieved the victory condition.\n\n"
                                "To play again, return to the main menu and start a new game.")
            return

        # Reset entity type bar maxes when returning to builder
        self.reset_entity_type_maxes()

        if self.game_state:
            self.game_state.offer_pending = True

            # Check for milestone achievements and show notification (BLOCKING)
            self._check_and_show_milestone_achievements_blocking()

        self.controller.switch_to_module("builder")

    # Keep all the existing methods for simulation processing, turn advancement, etc.
    # (All the existing methods from the original PlayModule remain unchanged)

    def advance_multiple_turns(self, num_turns):
        """Advance simulation by multiple turns - shows full output instantly (no delays)"""
        if not self.simulation_active or not self.simulation or self.game_won:
            return

        # Disable all control buttons during multi-turn processing
        self.set_control_buttons_state('disabled')

        try:
            # Process multiple turns using the same logic as next_turn() but without delays
            for turn_num in range(num_turns):
                if not self.simulation_active or self.simulation.is_simulation_over() or self.game_won:
                    break

                # Use the shared turn processing logic (without dramatic display)
                self._process_single_turn_fast()

                # Check victory condition after each turn
                if self._check_victory_condition():
                    break

                # Process UI updates for responsiveness
                self.frame.update_idletasks()

            # Check final conditions
            if self.game_won:
                self.show_victory_dialog()
            elif self.simulation.is_simulation_over():
                self.add_console_message("\n" + "=" * 50)
                self.add_console_message("EXTINCTION EVENT")
                self.add_console_message("=" * 50)
                self.add_console_message("No entities remaining - Your virus has gone extinct!")
                self.add_console_message("The simulation has ended.")
                self.add_console_message("")
                self.add_console_message("You can review the simulation results above.")
                self.add_console_message("When ready, confirm to return to the Builder.")

                self.simulation_active = False
                self.show_extinction_dialog()
            else:
                # Re-enable buttons if simulation is still active
                self.set_control_buttons_state('normal')

        except Exception as e:
            self.add_console_message(f"\nError during multi-turn advancement: {e}")
            self.set_control_buttons_state('normal')

    def _process_single_turn_fast(self):
        """Process a single turn quickly (for multi-turn advancement) - no delays"""
        # Process the turn
        turn_log = self.simulation.process_turn()

        # Extract entities created this turn from changes
        entities_created_this_turn = self._extract_entities_created(turn_log)

        # Update turn label and interferon display
        self.turn_label.config(text=f"Turn: {self.simulation.turn_count}")
        self.update_interferon_display()

        # Update milestone tracking
        if self.game_state:
            self.game_state.update_turn_count(self.simulation.turn_count)
            self.game_state.update_entity_counts(self.simulation.entities, entities_created_this_turn)

        # Add log to console (full output, same as single turn, but all at once)
        for message in turn_log:
            self.add_console_message(message)

        # Update displays - now uses the new bars
        self.update_entities_display(self.simulation.entities)

    def _process_single_turn_dramatic(self):
        """Process a single turn with dramatic timing - shows events gradually"""
        # Process the turn
        turn_log = self.simulation.process_turn()

        # Extract entities created this turn from changes
        entities_created_this_turn = self._extract_entities_created(turn_log)

        # Update turn label and interferon display
        self.turn_label.config(text=f"Turn: {self.simulation.turn_count}")
        self.update_interferon_display()

        # Update milestone tracking
        if self.game_state:
            self.game_state.update_turn_count(self.simulation.turn_count)
            self.game_state.update_entity_counts(self.simulation.entities, entities_created_this_turn)

        # Display log with dramatic timing
        self._display_turn_log_dramatically(turn_log)

        # Update displays - now uses the new bars
        self.update_entities_display(self.simulation.entities)

    def _display_turn_log_dramatically(self, turn_log):
        """Display turn log with dramatic pauses between sections"""
        if not turn_log:
            return

        # Parse the turn log into sections
        sections = self._parse_turn_log_into_sections(turn_log)

        # Display each section with delays
        for i, section in enumerate(sections):
            # Add the section messages
            for message in section:
                self.add_console_message(message)

            # Add delay between sections (but not after the last section)
            if i < len(sections) - 1:
                self.frame.update_idletasks()  # Update UI
                self.frame.after(100)  # 0.5 second delay
                # We need to use a different approach for the delay since after() is non-blocking
                import time
                time.sleep(0.1)

    def _parse_turn_log_into_sections(self, turn_log):
        """Parse turn log into logical sections for dramatic display"""
        sections = []
        current_section = []

        in_events = False
        in_population_end = False
        current_event = []

        for line in turn_log:
            line_content = line.strip()

            # Turn header (first section)
            if "TURN" in line_content and ("=" in line_content or "-" in line_content):
                if current_section:
                    sections.append(current_section)
                current_section = [line]
                in_events = False
                in_population_end = False
            elif line_content.startswith("TURN ") and not in_events and not in_population_end:
                current_section.append(line)
            elif "Events this turn:" in line_content:
                # End turn header section, start events section
                if current_section:
                    sections.append(current_section)
                current_section = [line]
                in_events = True
                in_population_end = False
            elif in_events and line_content.startswith("[") and "]" in line_content:
                # Start of a new event
                if current_event:
                    sections.append(current_event)
                current_event = [line]
            elif in_events and current_event and (line_content.startswith("Consumed:") or
                                                  line_content.startswith("Produced:") or
                                                  line_content.startswith("Degraded:") or
                                                  line_content.startswith("- ") or
                                                  line_content.startswith("+ ") or
                                                  line_content.startswith("  ") or  # Indented event details
                                                  "No events occurred" in line_content):
                current_event.append(line)
            elif "Population at end:" in line_content:
                # End current event
                if current_event:
                    sections.append(current_event)
                    current_event = []
                elif in_events and current_section:  # Events section with no events
                    sections.append(current_section)
                # Start final population section
                current_section = [line]
                in_events = False
                in_population_end = True
            elif in_population_end:
                current_section.append(line)
            else:
                # Default: add to current section
                if current_event:
                    current_event.append(line)
                else:
                    current_section.append(line)

        # Add any remaining sections
        if current_event:
            sections.append(current_event)
        if current_section:
            sections.append(current_section)

        return sections

    def set_control_buttons_state(self, state):
        """Enable or disable all control buttons"""
        buttons = [self.next_turn_btn, self.advance_3_btn, self.advance_10_btn]
        for button in buttons:
            button.config(state=state)

    def set_virus_blueprint(self, virus_blueprint):
        """Set the virus blueprint and initialize simulation"""
        self.virus_blueprint = virus_blueprint
        self.initialize_simulation()

    def initialize_simulation(self):
        """Initialize the simulation with virus blueprint"""
        if not hasattr(self, 'virus_blueprint'):
            self.virus_blueprint = {
                "starting_entities": {"unenveloped virion (extracellular)": 10},
                "possible_entities": ["unenveloped virion (extracellular)"],
                "transition_rules": [],
                "genes": []
            }

        # Create ViralSimulation and set database manager for location data
        self.simulation = ViralSimulation(self.virus_blueprint)
        if hasattr(self.simulation, 'db_manager'):
            self.simulation.db_manager = self.db_manager
        else:
            self.simulation.db_manager = self.db_manager
        self.simulation_active = True
        self.game_won = False

        # Reset entity type maxes for new simulation
        self.reset_entity_type_maxes()

        # Enable control buttons
        self.set_control_buttons_state('normal')

        # Reset milestone progress for this play run
        if self.game_state:
            self.game_state.reset_milestone_progress()

        # Clear console
        self.console_text.config(state='normal')
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state='disabled')

        # Update displays
        self.turn_label.config(text=f"Turn: {self.simulation.turn_count}")
        self.update_interferon_display()
        self.update_entities_display(self.simulation.entities)  # Now uses bars

        # Enhanced intro messages
        self.add_console_message("=" * 70)
        self.add_console_message("  VIRUS SIMULATION INITIALIZED")
        self.add_console_message("=" * 70)
        self.add_console_message("Initial infection beginning...")

        if self.virus_blueprint.get("genes"):
            self.add_console_message(f"Virus genes: {', '.join(self.virus_blueprint['genes'])}")
        else:
            self.add_console_message("Virus has no genes - only basic structure")

        # Show initial population
        total_entities = sum(self.simulation.entities.values())
        self.add_console_message(f"Starting population: {total_entities} entities")
        self.add_console_message("")

        # Initial milestone tracking (turn 0 with starting entities)
        if self.game_state:
            self.game_state.update_turn_count(0)
            self.game_state.update_entity_counts(self.simulation.entities)

    def update_interferon_display(self):
        """Update the interferon level indicator"""
        if not self.simulation:
            self.interferon_label.config(text="Interferon: --/100", foreground="#6b7280")
            return

        interferon_level = self.simulation.get_interferon_level()

        # Color coding based on interferon level
        if interferon_level >= 75.0:
            color = "#dc2626"  # Red - high interferon
            intensity = "HIGH"
        elif interferon_level >= 50.0:
            color = "#ea580c"  # Orange - medium interferon
        elif interferon_level >= 25.0:
            color = "#ca8a04"  # Yellow - low interferon
        elif interferon_level > 0.0:
            color = "#16a34a"  # Green - minimal interferon
        else:
            color = "#6b7280"  # Gray - no interferon
            intensity = "NONE"

        # Format display text
        if interferon_level >= 75.0:
            display_text = f"Interferon: {interferon_level:.1f}/100 ({intensity})"
        else:
            display_text = f"Interferon: {interferon_level:.1f}/100"

        self.interferon_label.config(text=display_text, foreground=color)

    def next_turn(self):
        """Process next turn of simulation with dramatic display"""
        if not self.simulation_active or not self.simulation or self.game_won:
            return

        # Use the dramatic turn processing
        self._process_single_turn_dramatic()

        # Check victory condition after processing turn
        if self._check_victory_condition():
            self.show_victory_dialog()
            return

        # If simulation naturally ends (no entities), show confirmation dialog
        if self.simulation.is_simulation_over():
            self.add_console_message("\n" + "=" * 50)
            self.add_console_message("EXTINCTION EVENT")
            self.add_console_message("=" * 50)
            self.add_console_message("No entities remaining - Your virus has gone extinct!")
            self.add_console_message("The simulation has ended.")
            self.add_console_message("")
            self.add_console_message("You can review the simulation results above.")
            self.add_console_message("When ready, confirm to return to the Builder.")

            self.simulation_active = False
            self.set_control_buttons_state('disabled')

            # Show extinction confirmation dialog
            self.show_extinction_dialog()

    def _check_victory_condition(self):
        """Check if victory condition (10,000 entities) has been reached"""
        if not self.simulation or self.game_won:
            return False

        total_entities = sum(self.simulation.entities.values())
        if total_entities >= 10000:
            self.game_won = True
            self.simulation_active = False
            self.set_control_buttons_state('disabled')
            self.exit_btn.config(state='disabled')
            return True
        return False

    def show_victory_dialog(self):
        """Show congratulatory dialog when victory condition is reached"""
        self.add_console_message("\n" + "=" * 50)
        self.add_console_message("RUNAWAY REACTION ACHIEVED!")
        self.add_console_message("=" * 50)
        self.add_console_message("You have created a runaway reaction and reached 10,000 entities!")
        self.add_console_message("Congratulations! Your virus has succeeded beyond all expectations!")
        self.add_console_message("")

        dialog = tk.Toplevel(self.frame)
        dialog.title("VICTORY!")
        dialog.geometry("500x400")
        dialog.transient(self.frame)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (250)
        y = (dialog.winfo_screenheight() // 2) - (200)
        dialog.geometry(f"500x400+{x}+{y}")

        # Header with victory styling
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(header_frame, text="🎉 VICTORY! 🎉", font=("Arial", 18, "bold"),
                  foreground="green").pack()

        # Victory message
        message_frame = ttk.Frame(dialog)
        message_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        victory_text = (
            "Congratulations!\n\n"
            "You have created a runaway reaction and reached 10,000 entities!\n\n"
            f"Your virus achieved this incredible feat in just {self.simulation.turn_count} turns!\n\n"
            "This represents a complete biological victory - your virus has "
            "overwhelmed all natural limitations and achieved exponential growth."
        )

        ttk.Label(message_frame, text=victory_text, font=("Arial", 11),
                  justify=tk.CENTER, wraplength=450).pack()

        # Entity production statistics
        if self.game_state and (self.game_state.cumulative_entity_counts or self.game_state.peak_entity_counts):
            stats_frame = ttk.LabelFrame(message_frame, text="Final Production Statistics", padding=10)
            stats_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

            # Create text widget for statistics with scrollbar
            text_frame = ttk.Frame(stats_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)

            stats_text = tk.Text(text_frame, height=6, width=50, state='disabled',
                                 font=("Consolas", 9), wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=stats_text.yview)
            stats_text.config(yscrollcommand=scrollbar.set)

            stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Populate statistics
            stats_text.config(state='normal')

            # Get all entity classes that were produced or had peaks
            all_classes = set(self.game_state.cumulative_entity_counts.keys()) | set(
                self.game_state.peak_entity_counts.keys())

            if all_classes:
                stats_text.insert(tk.END, "Produced in total this round: (peak)\n")
                stats_text.insert(tk.END, "-" * 35 + "\n")

                # Sort classes by total produced (descending), then by name
                sorted_classes = sorted(all_classes,
                                        key=lambda x: (-self.game_state.cumulative_entity_counts.get(x, 0), x))

                for entity_class in sorted_classes:
                    total = self.game_state.cumulative_entity_counts.get(entity_class, 0)
                    peak = self.game_state.peak_entity_counts.get(entity_class, 0)

                    # Only show if there was some production or peak
                    if total > 0 or peak > 0:
                        stats_text.insert(tk.END, f"{entity_class:12} {total:4d} ({peak:2d})\n")

            stats_text.config(state='disabled')

        # Game over notice
        ending_frame = ttk.Frame(message_frame)
        ending_frame.pack(fill=tk.X, pady=(15, 0))

        ending_text = ("This simulation session is now complete. You have achieved "
                       "the ultimate victory condition!")
        ttk.Label(ending_frame, text=ending_text, font=("Arial", 10, "bold"),
                  justify=tk.CENTER, wraplength=450, foreground="blue").pack()

        # Close button
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(button_frame, text="Close Simulation",
                   command=lambda: self._close_victory_dialog(dialog)).pack()

        # Auto-focus and handle escape key
        dialog.focus_set()
        dialog.bind('<Escape>', lambda e: self._close_victory_dialog(dialog))

    def _close_victory_dialog(self, dialog):
        """Close victory dialog and end the session"""
        dialog.destroy()
        # Show final message about the completed session
        self.add_console_message("")
        self.add_console_message("Simulation session completed with VICTORY!")
        self.add_console_message("All controls have been disabled.")
        self.add_console_message("")
        self.add_console_message("To play again, return to the main menu and start a new game.")

    def show_extinction_dialog(self):
        """Show confirmation dialog when virus goes extinct"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Simulation Complete")
        dialog.geometry("500x400")
        dialog.transient(self.frame)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (250)
        y = (dialog.winfo_screenheight() // 2) - (200)
        dialog.geometry(f"500x400+{x}+{y}")

        # Icon and header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(header_frame, text="Virus Extinction", font=("Arial", 16, "bold"),
                  foreground="red").pack()

        # Message
        message_frame = ttk.Frame(dialog)
        message_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        message_text = (
            f"Your virus has gone extinct!\n\n"
            f"The simulation ran for {self.simulation.turn_count} turns before "
            "all viral entities were eliminated.\n"
        )

        ttk.Label(message_frame, text=message_text, font=("Arial", 11),
                  justify=tk.CENTER, wraplength=450).pack()

        # Entity production statistics
        if self.game_state and (self.game_state.cumulative_entity_counts or self.game_state.peak_entity_counts):
            stats_frame = ttk.LabelFrame(message_frame, text="Entity Production Statistics", padding=10)
            stats_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

            # Create text widget for statistics with scrollbar
            text_frame = ttk.Frame(stats_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)

            stats_text = tk.Text(text_frame, height=8, width=50, state='disabled',
                                 font=("Consolas", 9), wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=stats_text.yview)
            stats_text.config(yscrollcommand=scrollbar.set)

            stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Populate statistics
            stats_text.config(state='normal')

            # Get all entity classes that were produced or had peaks
            all_classes = set(self.game_state.cumulative_entity_counts.keys()) | set(
                self.game_state.peak_entity_counts.keys())

            if all_classes:
                stats_text.insert(tk.END, "Produced in total this round: (peak)\n")
                stats_text.insert(tk.END, "-" * 35 + "\n")

                # Sort classes by total produced (descending), then by name
                sorted_classes = sorted(all_classes,
                                        key=lambda x: (-self.game_state.cumulative_entity_counts.get(x, 0), x))

                for entity_class in sorted_classes:
                    total = self.game_state.cumulative_entity_counts.get(entity_class, 0)
                    peak = self.game_state.peak_entity_counts.get(entity_class, 0)

                    # Only show if there was some production or peak
                    if total > 0 or peak > 0:
                        stats_text.insert(tk.END, f"{entity_class:12} {total:4d} ({peak:2d})\n")
            else:
                stats_text.insert(tk.END, "No entities were produced during this simulation.")

            stats_text.config(state='disabled')

        # Closing message
        closing_frame = ttk.Frame(message_frame)
        closing_frame.pack(fill=tk.X, pady=(15, 0))

        closing_text = ("Take a moment to review the simulation log to understand "
                        "what happened, then return to the Builder to try again.")
        ttk.Label(closing_frame, text=closing_text, font=("Arial", 10),
                  justify=tk.CENTER, wraplength=450).pack()

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(button_frame, text="Review Results",
                   command=dialog.destroy).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="Return to Builder",
                   command=lambda: self.confirm_return_to_builder(dialog)).pack(side=tk.RIGHT)

        # Auto-focus and handle escape key
        dialog.focus_set()
        dialog.bind('<Escape>', lambda e: dialog.destroy())

    def confirm_return_to_builder(self, dialog):
        """Confirm return to builder and close dialog"""
        dialog.destroy()
        self.exit_to_builder()

    def add_console_message(self, message):
        self.console_text.config(state='normal')
        self.console_text.insert(tk.END, message + "\n")
        self.console_text.see(tk.END)
        self.console_text.config(state='disabled')

    def _extract_entities_created(self, turn_log: list[str]) -> dict[str, int]:
        """Extract entities created this turn from the simulation log"""
        entities_created: dict[str, int] = {}

        for raw in turn_log:
            line = raw.strip()

            # Single-line: "Produced: 2 viral RNA (cytoplasm)"
            if line.startswith("Produced:"):
                content = line[len("Produced:"):].strip()
                if content:
                    parts = content.split(" ", 1)
                    if len(parts) == 2:
                        count_str, entity_name = parts
                        try:
                            count = int(count_str)
                            entities_created[entity_name] = entities_created.get(entity_name, 0) + count
                        except ValueError:
                            pass
                continue

            # Multi-line item: "+ 2 viral RNA (cytoplasm)"
            l = raw.lstrip()
            if l.startswith("+"):
                content = l[1:].strip()  # drop '+'
                parts = content.split(" ", 1)
                if len(parts) == 2:
                    count_str, entity_name = parts
                    try:
                        count = int(count_str)
                        entities_created[entity_name] = entities_created.get(entity_name, 0) + count
                    except ValueError:
                        pass

        return entities_created

    def _check_and_show_milestone_achievements_blocking(self):
        """Check for milestone achievements and show notification dialog (BLOCKING VERSION)"""
        if not self.game_state:
            return

        # Get all milestone progress data
        progress_data = self.game_state.get_milestone_progress()
        newly_achieved = progress_data.get("newly_achieved_this_run", [])
        open_milestones = progress_data.get("open", [])

        # Only show dialog if there are milestones to display
        if not newly_achieved and not open_milestones:
            return

        # Create achievement/progress notification dialog (BLOCKING)
        self._show_milestone_dialog_blocking(newly_achieved, open_milestones, progress_data)

        # Award EP for newly achieved milestones
        if newly_achieved:
            self.game_state.award_milestone_achievements()

    def _show_milestone_dialog_blocking(self, newly_achieved: list[dict], open_milestones: list[dict],
                                        progress_data: dict):
        """Show a dialog listing milestone achievements and open milestones from this run (BLOCKING VERSION)"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Milestone Progress")
        dialog.geometry("600x500")
        dialog.transient(self.frame)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (300)
        y = (dialog.winfo_screenheight() // 2) - (250)
        dialog.geometry(f"600x500+{x}+{y}")

        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        if newly_achieved:
            ttk.Label(header_frame, text="Milestones Achieved!", font=("Arial", 16, "bold")).pack()
            total_ep = sum(m["reward_ep"] for m in newly_achieved)
            ttk.Label(header_frame, text=f"You earned {total_ep} Evolution Points!",
                      font=("Arial", 12), foreground="green").pack(pady=(5, 0))
        else:
            ttk.Label(header_frame, text="Milestone Progress", font=("Arial", 16, "bold")).pack()
            ttk.Label(header_frame, text="Keep working towards your goals!",
                      font=("Arial", 12), foreground="blue").pack(pady=(5, 0))

        # Create notebook for tabs
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Achievements tab (only if there are achievements)
        if newly_achieved:
            achievements_frame = ttk.Frame(notebook)
            notebook.add(achievements_frame, text=f"Achieved ({len(newly_achieved)})")

            achievements_text = scrolledtext.ScrolledText(achievements_frame, height=15, wrap=tk.WORD, state='disabled')
            achievements_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Populate achievements
            achievements_text.config(state='normal')
            for milestone in newly_achieved:
                name = milestone["name"]
                desc = milestone["description"]
                reward = milestone["reward_ep"]

                achievements_text.insert(tk.END, f"[ACHIEVED] {name}\n")
                achievements_text.insert(tk.END, f"   {desc}\n")
                achievements_text.insert(tk.END, f"   Reward: +{reward} EP\n\n")
            achievements_text.config(state='disabled')

        # Open milestones tab (only if there are open milestones)
        if open_milestones:
            open_frame = ttk.Frame(notebook)
            notebook.add(open_frame, text=f"In Progress ({len(open_milestones)})")

            open_text = scrolledtext.ScrolledText(open_frame, height=15, wrap=tk.WORD, state='disabled')
            open_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Populate open milestones with progress
            open_text.config(state='normal')
            for milestone in open_milestones:
                name = milestone["name"]
                desc = milestone["description"]
                reward = milestone["reward_ep"]
                progress_desc = milestone.get("progress_description", "No progress")

                open_text.insert(tk.END, f"[IN PROGRESS] {name}\n")
                open_text.insert(tk.END, f"   {desc}\n")
                open_text.insert(tk.END, f"   Progress: {progress_desc}\n")
                open_text.insert(tk.END, f"   Reward: {reward} EP\n\n")
            open_text.config(state='disabled')

        # Progress summary
        if self.game_state:
            achieved_count = len(progress_data.get("achieved", []))
            total_count = achieved_count + len(open_milestones)
            total_ep = progress_data.get("total_ep_earned", 0)

            summary_text = f"Overall Progress: {achieved_count}/{total_count} milestones completed ({total_ep} EP earned)"
            ttk.Label(dialog, text=summary_text, font=("Arial", 10, "italic")).pack(pady=(0, 10))

        # Close button
        ttk.Button(dialog, text="Continue", command=dialog.destroy).pack(pady=(0, 20))

        # Auto-focus and handle escape key
        dialog.focus_set()
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        # CRITICAL: Wait for dialog to close before continuing (makes it blocking)
        self.frame.wait_window(dialog)


class EditorModule(GameModule):
    """Gene database editor module with tabs for entities, genes, and milestones - WITH MILESTONE SUPPORT, INTERFERON DESCRIPTIONS, AND POLYMERASE GENE SUPPORT"""

    def __init__(self, parent, controller):
        self.db_manager = GeneDatabaseManager()
        self.current_entity_name = None  # Track currently selected entity
        self.current_gene_name = None  # Track currently selected gene
        self.current_milestone_id = None  # Track currently selected milestone
        super().__init__(parent, controller)

    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(header_frame, text="Gene Database Editor", font=("Arial", 16, "bold")).pack(side=tk.LEFT)

        # File operations
        file_frame = ttk.Frame(header_frame)
        file_frame.pack(side=tk.RIGHT)

        ttk.Button(file_frame, text="New Database", command=self.new_database).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="Open", command=self.open_database).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="Save", command=self.save_database).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="Save As", command=self.save_as_database).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_frame, text="← Menu", command=lambda: self.controller.switch_to_module("menu")).pack(
            side=tk.LEFT, padx=(10, 2))

        # Database info frame
        info_frame = ttk.LabelFrame(self.frame, text="Database Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)

        # Database name and version
        ttk.Label(info_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.db_name_var = tk.StringVar()
        self.db_name_entry = ttk.Entry(info_grid, textvariable=self.db_name_var, width=30)
        self.db_name_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(info_grid, text="Version:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.db_version_var = tk.StringVar()
        self.db_version_entry = ttk.Entry(info_grid, textvariable=self.db_version_var, width=10)
        self.db_version_entry.grid(row=0, column=3, sticky=tk.W)

        # Description
        ttk.Label(info_grid, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=(0, 5), pady=(10, 0))
        self.db_desc_text = tk.Text(info_grid, height=2, width=60)
        self.db_desc_text.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(10, 0))

        # Status
        self.status_label = ttk.Label(info_frame, text="No database loaded", font=("Arial", 10, "italic"))
        self.status_label.pack(anchor=tk.W, pady=(10, 0))

        # Main content area with tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Entities tab
        self.entities_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.entities_frame, text="Entities")
        self.setup_entities_tab()

        # Genes tab
        self.genes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.genes_frame, text="Genes")
        self.setup_genes_tab()

        # Milestones tab
        self.milestones_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.milestones_frame, text="Milestones")
        self.setup_milestones_tab()

        # Initialize displays
        self.update_database_display()
        self.update_entity_list()
        self.update_gene_list()
        self.update_milestone_list()
        self.clear_entity_form()
        self.clear_gene_form()
        self.clear_milestone_form()

    def setup_entities_tab(self):
        """Setup the entities tab - WITH STARTER ENTITY CHECKBOX"""
        # Main layout
        main_frame = ttk.Frame(self.entities_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Entity list
        left_frame = ttk.LabelFrame(main_frame, text="Entities", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # Entity list with scrollbar
        entity_list_frame = ttk.Frame(left_frame)
        entity_list_frame.pack(fill=tk.BOTH, expand=True)

        self.entity_listbox = tk.Listbox(entity_list_frame, width=35, height=20)
        self.entity_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Multiple event bindings
        self.entity_listbox.bind('<<ListboxSelect>>', self.on_entity_select)
        self.entity_listbox.bind('<Button-1>', self.on_entity_click)
        self.entity_listbox.bind('<ButtonRelease-1>', self.on_entity_click)
        self.entity_listbox.bind('<Double-Button-1>', self.on_entity_double_click)

        entity_scrollbar = ttk.Scrollbar(entity_list_frame, orient=tk.VERTICAL, command=self.entity_listbox.yview)
        entity_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.entity_listbox.config(yscrollcommand=entity_scrollbar.set)

        # Entity management buttons
        entity_btn_frame = ttk.Frame(left_frame)
        entity_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(entity_btn_frame, text="New Entity", command=self.new_entity).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(entity_btn_frame, text="Clone Entity", command=self.clone_entity).pack(side=tk.LEFT, padx=(0, 5))

        # Instructions
        ttk.Label(left_frame, text="Click entity to edit →", font=("Arial", 9, "italic")).pack(pady=(5, 0))

        # Right panel - Entity editor
        self.entity_editor_frame = ttk.LabelFrame(main_frame, text="Entity Editor", padding=10)
        self.entity_editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Simple status label
        self.entity_status_label = ttk.Label(self.entity_editor_frame, text="No entity selected",
                                             font=("Arial", 10, "italic"))
        self.entity_status_label.pack(anchor=tk.W, pady=(0, 10))

        # Entity properties
        props_frame = ttk.LabelFrame(self.entity_editor_frame, text="Entity Properties", padding=10)
        props_frame.pack(fill=tk.X, pady=(0, 10))

        props_grid = ttk.Frame(props_frame)
        props_grid.pack(fill=tk.X)

        # Entity name
        ttk.Label(props_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.entity_name_var = tk.StringVar()
        self.entity_name_entry = ttk.Entry(props_grid, textvariable=self.entity_name_var, width=40)
        self.entity_name_entry.grid(row=0, column=1, columnspan=3, sticky=tk.W, pady=(0, 5))

        # Description
        ttk.Label(props_grid, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=(0, 5))
        self.entity_desc_text = tk.Text(props_grid, height=3, width=50)
        self.entity_desc_text.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(0, 5))

        # Degradation rate
        ttk.Label(props_grid, text="Base Degradation Rate:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5),
                                                                  pady=(5, 0))
        self.degradation_var = tk.DoubleVar(value=0.05)
        degradation_frame = ttk.Frame(props_grid)
        degradation_frame.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))

        ttk.Entry(degradation_frame, textvariable=self.degradation_var, width=10).pack(side=tk.LEFT)
        ttk.Label(degradation_frame, text="(0.0 - 1.0)", font=("Arial", 9, "italic")).pack(side=tk.LEFT, padx=(5, 0))

        # Location
        ttk.Label(props_grid, text="Location:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.location_var = tk.StringVar()
        location_combo = ttk.Combobox(props_grid, textvariable=self.location_var, width=20)
        location_combo['values'] = ('extracellular', 'cytoplasm', 'endosome', 'nucleus', 'membrane', 'unknown')
        location_combo.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))

        # Entity class
        ttk.Label(props_grid, text="Entity Class:").grid(row=3, column=2, sticky=tk.W, padx=(20, 5), pady=(5, 0))
        self.entity_class_var = tk.StringVar()
        class_combo = ttk.Combobox(props_grid, textvariable=self.entity_class_var, width=15)
        class_combo['values'] = ('virion', 'protein', 'RNA', 'DNA', 'complex', 'unknown')
        class_combo.grid(row=3, column=3, sticky=tk.W, pady=(5, 0))

        # Starter entity checkbox
        ttk.Label(props_grid, text="Starter Entity:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.is_starter_var = tk.BooleanVar()
        starter_checkbox = ttk.Checkbutton(props_grid, text="Can be used as starting entity",
                                           variable=self.is_starter_var)
        starter_checkbox.grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))

        # Help text for starter entities
        help_text = ttk.Label(props_grid,
                              text="Starter entities can be selected as initial entities when building a virus",
                              font=("Arial", 9, "italic"), foreground="gray")
        help_text.grid(row=5, column=1, columnspan=3, sticky=tk.W, pady=(5, 0))

        # Simple button layout
        button_frame = ttk.Frame(self.entity_editor_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save", command=self.save_entity).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Save as New", command=self.save_entity_as_new).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear", command=self.clear_entity_form).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete", command=self.delete_entity).pack(side=tk.LEFT)

    def setup_genes_tab(self):
        """Setup the genes tab - UPDATED WITH POLYMERASE CHECKBOX"""
        # Main layout
        main_frame = ttk.Frame(self.genes_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Gene list
        left_frame = ttk.LabelFrame(main_frame, text="Genes", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # Gene list with scrollbar
        gene_list_frame = ttk.Frame(left_frame)
        gene_list_frame.pack(fill=tk.BOTH, expand=True)

        self.gene_listbox = tk.Listbox(gene_list_frame, width=35, height=20)
        self.gene_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Multiple event bindings
        self.gene_listbox.bind('<<ListboxSelect>>', self.on_gene_select)
        self.gene_listbox.bind('<Button-1>', self.on_gene_click)
        self.gene_listbox.bind('<ButtonRelease-1>', self.on_gene_click)
        self.gene_listbox.bind('<Double-Button-1>', self.on_gene_double_click)

        gene_scrollbar = ttk.Scrollbar(gene_list_frame, orient=tk.VERTICAL, command=self.gene_listbox.yview)
        gene_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.gene_listbox.config(yscrollcommand=gene_scrollbar.set)

        # Gene management buttons
        gene_btn_frame = ttk.Frame(left_frame)
        gene_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(gene_btn_frame, text="New Gene", command=self.new_gene).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gene_btn_frame, text="Clone Gene", command=self.clone_gene).pack(side=tk.LEFT, padx=(0, 5))

        # Instructions
        ttk.Label(left_frame, text="Click gene to edit →", font=("Arial", 9, "italic")).pack(pady=(5, 0))

        # Right panel - Gene editor
        self.gene_editor_frame = ttk.LabelFrame(main_frame, text="Gene Editor", padding=10)
        self.gene_editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Simple status label
        self.gene_status_label = ttk.Label(self.gene_editor_frame, text="No gene selected",
                                           font=("Arial", 10, "italic"))
        self.gene_status_label.pack(anchor=tk.W, pady=(0, 10))

        # Gene properties
        props_frame = ttk.LabelFrame(self.gene_editor_frame, text="Gene Properties", padding=10)
        props_frame.pack(fill=tk.X, pady=(0, 10))

        props_grid = ttk.Frame(props_frame)
        props_grid.pack(fill=tk.X)

        # Gene name
        ttk.Label(props_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.gene_name_var = tk.StringVar()
        self.gene_name_entry = ttk.Entry(props_grid, textvariable=self.gene_name_var, width=30)
        self.gene_name_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        # Gene cost
        ttk.Label(props_grid, text="Cost:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.gene_cost_var = tk.IntVar()
        self.gene_cost_entry = ttk.Entry(props_grid, textvariable=self.gene_cost_var, width=10)
        self.gene_cost_entry.grid(row=0, column=3, sticky=tk.W)

        # Gene description
        ttk.Label(props_grid, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=(0, 5), pady=(10, 0))
        self.gene_desc_text = tk.Text(props_grid, height=3, width=60)
        self.gene_desc_text.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(10, 0))

        # Prerequisites
        ttk.Label(props_grid, text="Prerequisites:").grid(row=2, column=0, sticky=tk.NW, padx=(0, 5), pady=(10, 0))
        prereq_frame = ttk.Frame(props_grid)
        prereq_frame.grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=(10, 0))

        self.prereq_listbox = tk.Listbox(prereq_frame, height=3, width=40)
        self.prereq_listbox.pack(side=tk.LEFT)

        prereq_btn_frame = ttk.Frame(prereq_frame)
        prereq_btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))

        ttk.Button(prereq_btn_frame, text="Add", command=self.add_prerequisite).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(prereq_btn_frame, text="Remove", command=self.remove_prerequisite).pack(fill=tk.X)

        # NEW: Polymerase gene checkbox
        ttk.Label(props_grid, text="Polymerase Gene:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.is_polymerase_var = tk.BooleanVar()
        polymerase_checkbox = ttk.Checkbutton(props_grid, text="This is a polymerase gene (limit: 1 per virus)",
                                              variable=self.is_polymerase_var)
        polymerase_checkbox.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))

        # Help text for polymerase genes
        polymerase_help_text = ttk.Label(props_grid,
                                         text="Only one polymerase gene can be installed in a virus at a time",
                                         font=("Arial", 9, "italic"), foreground="gray")
        polymerase_help_text.grid(row=4, column=1, columnspan=3, sticky=tk.W, pady=(5, 0))

        # Effects section
        effects_frame = ttk.LabelFrame(self.gene_editor_frame, text="Gene Effects", padding=10)
        effects_frame.pack(fill=tk.BOTH, expand=True)

        # Effects list
        effects_list_frame = ttk.Frame(effects_frame)
        effects_list_frame.pack(fill=tk.X, pady=(0, 10))

        self.effects_listbox = tk.Listbox(effects_list_frame, height=6)
        self.effects_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.effects_listbox.bind('<<ListboxSelection>>', self.on_effect_select)

        effects_btn_frame = ttk.Frame(effects_list_frame)
        effects_btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        ttk.Button(effects_btn_frame, text="Add Effect", command=self.add_effect).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(effects_btn_frame, text="Edit Effect", command=self.edit_effect).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(effects_btn_frame, text="Remove Effect", command=self.remove_effect).pack(fill=tk.X)

        # Simple button layout
        gene_button_frame = ttk.Frame(self.gene_editor_frame)
        gene_button_frame.pack(pady=10)

        ttk.Button(gene_button_frame, text="Save", command=self.save_gene).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gene_button_frame, text="Save as New", command=self.save_gene_as_new).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gene_button_frame, text="Clear", command=self.clear_gene_form).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gene_button_frame, text="Delete", command=self.delete_gene).pack(side=tk.LEFT)

    def setup_milestones_tab(self):
        """Setup the milestones tab"""
        # Main layout
        main_frame = ttk.Frame(self.milestones_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Milestone list
        left_frame = ttk.LabelFrame(main_frame, text="Milestones", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # Milestone list with scrollbar
        milestone_list_frame = ttk.Frame(left_frame)
        milestone_list_frame.pack(fill=tk.BOTH, expand=True)

        self.milestone_listbox = tk.Listbox(milestone_list_frame, width=35, height=20)
        self.milestone_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Multiple event bindings
        self.milestone_listbox.bind('<<ListboxSelect>>', self.on_milestone_select)
        self.milestone_listbox.bind('<Button-1>', self.on_milestone_click)
        self.milestone_listbox.bind('<ButtonRelease-1>', self.on_milestone_click)
        self.milestone_listbox.bind('<Double-Button-1>', self.on_milestone_double_click)

        milestone_scrollbar = ttk.Scrollbar(milestone_list_frame, orient=tk.VERTICAL,
                                            command=self.milestone_listbox.yview)
        milestone_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.milestone_listbox.config(yscrollcommand=milestone_scrollbar.set)

        # Milestone management buttons
        milestone_btn_frame = ttk.Frame(left_frame)
        milestone_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(milestone_btn_frame, text="New Milestone", command=self.new_milestone).pack(side=tk.LEFT,
                                                                                               padx=(0, 5))
        ttk.Button(milestone_btn_frame, text="Clone Milestone", command=self.clone_milestone).pack(side=tk.LEFT,
                                                                                                   padx=(0, 5))

        # Instructions
        ttk.Label(left_frame, text="Click milestone to edit →", font=("Arial", 9, "italic")).pack(pady=(5, 0))

        # Right panel - Milestone editor
        self.milestone_editor_frame = ttk.LabelFrame(main_frame, text="Milestone Editor", padding=10)
        self.milestone_editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Simple status label
        self.milestone_status_label = ttk.Label(self.milestone_editor_frame, text="No milestone selected",
                                                font=("Arial", 10, "italic"))
        self.milestone_status_label.pack(anchor=tk.W, pady=(0, 10))

        # Milestone properties
        props_frame = ttk.LabelFrame(self.milestone_editor_frame, text="Milestone Properties", padding=10)
        props_frame.pack(fill=tk.X, pady=(0, 10))

        props_grid = ttk.Frame(props_frame)
        props_grid.pack(fill=tk.X)

        # Milestone ID and Name
        ttk.Label(props_grid, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.milestone_id_var = tk.StringVar()
        self.milestone_id_entry = ttk.Entry(props_grid, textvariable=self.milestone_id_var, width=20)
        self.milestone_id_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(props_grid, text="Name:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.milestone_name_var = tk.StringVar()
        self.milestone_name_entry = ttk.Entry(props_grid, textvariable=self.milestone_name_var, width=25)
        self.milestone_name_entry.grid(row=0, column=3, sticky=tk.W)

        # Description
        ttk.Label(props_grid, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=(0, 5), pady=(10, 0))
        self.milestone_desc_text = tk.Text(props_grid, height=3, width=60)
        self.milestone_desc_text.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(10, 0))

        # Milestone type
        ttk.Label(props_grid, text="Type:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.milestone_type_var = tk.StringVar()
        self.milestone_type_combo = ttk.Combobox(props_grid, textvariable=self.milestone_type_var, width=25,
                                                 state="readonly")
        self.milestone_type_combo['values'] = ('survive_turns', 'peak_entity_count', 'cumulative_entity_count')
        self.milestone_type_combo.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))
        self.milestone_type_combo.bind('<<ComboboxSelected>>', self.on_milestone_type_change)

        # Target and Reward
        ttk.Label(props_grid, text="Target:").grid(row=2, column=2, sticky=tk.W, padx=(20, 5), pady=(10, 0))
        self.milestone_target_var = tk.IntVar(value=5)
        self.milestone_target_entry = ttk.Entry(props_grid, textvariable=self.milestone_target_var, width=10)
        self.milestone_target_entry.grid(row=2, column=3, sticky=tk.W, pady=(10, 0))

        ttk.Label(props_grid, text="Reward EP:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.milestone_reward_var = tk.IntVar(value=25)
        self.milestone_reward_entry = ttk.Entry(props_grid, textvariable=self.milestone_reward_var, width=10)
        self.milestone_reward_entry.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))

        # Entity class (conditional)
        ttk.Label(props_grid, text="Entity Class:").grid(row=3, column=2, sticky=tk.W, padx=(20, 5), pady=(5, 0))
        self.milestone_entity_class_var = tk.StringVar()
        self.milestone_entity_class_combo = ttk.Combobox(props_grid, textvariable=self.milestone_entity_class_var,
                                                         width=15, state="readonly")
        self.milestone_entity_class_combo.grid(row=3, column=3, sticky=tk.W, pady=(5, 0))

        # Help text frame
        self.milestone_help_frame = ttk.Frame(props_grid)
        self.milestone_help_frame.grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=(10, 0))

        self.milestone_help_label = ttk.Label(self.milestone_help_frame,
                                              text="Select a milestone type to see specific instructions",
                                              font=("Arial", 9, "italic"), foreground="gray")
        self.milestone_help_label.pack(anchor=tk.W)

        # Simple button layout
        button_frame = ttk.Frame(self.milestone_editor_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save", command=self.save_milestone).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Save as New", command=self.save_milestone_as_new).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear", command=self.clear_milestone_form).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete", command=self.delete_milestone).pack(side=tk.LEFT)

    # =================== EFFECT DESCRIPTION WITH INTERFERON SUPPORT ===================

    def format_effect_description(self, effect):
        """Format effect for display in list - WITH INTERFERON SUPPORT"""
        effect_type = effect.get("type", "unknown")

        if effect_type == "enable_entity":
            return f"Enable: {effect.get('entity', 'Unknown')}"
        elif effect_type == "add_transition":
            rule = effect.get("rule", {})
            rule_name = rule.get("name", "Unknown")

            # Get inputs and outputs for enhanced display
            inputs = rule.get("inputs", [])
            outputs = rule.get("outputs", [])

            # Build compact summary showing entity counts
            input_summary = ""
            if inputs:
                if len(inputs) == 1:
                    input_summary = f"1 input"
                else:
                    input_summary = f"{len(inputs)} inputs"

            output_summary = ""
            if outputs:
                if len(outputs) == 1:
                    output_summary = f"1 output"
                else:
                    output_summary = f"{len(outputs)} outputs"

            # Check for interferon
            interferon_amount = rule.get("interferon_amount", 0.0)
            interferon_part = ""
            if interferon_amount > 0:
                interferon_part = f", IFN: {interferon_amount:.2f}"

            # Build final description
            if input_summary and output_summary:
                return f"Transition: {rule_name} ({input_summary} → {output_summary}{interferon_part})"
            elif input_summary:
                return f"Transition: {rule_name} ({input_summary}{interferon_part})"
            else:
                return f"Transition: {rule_name}{interferon_part}"

        elif effect_type == "modify_transition":
            rule_name = effect.get("rule_name", "Unknown")
            modification = effect.get("modification", {})

            # Check for modifications
            prob_mult = modification.get("probability_multiplier", 1.0)
            ifn_mult = modification.get("interferon_multiplier", 1.0)

            mod_parts = []
            if prob_mult != 1.0:
                mod_parts.append(f"prob×{prob_mult:.1f}")
            if ifn_mult != 1.0:
                mod_parts.append(f"IFN×{ifn_mult:.2f}")

            if mod_parts:
                return f"Modify: {rule_name} ({', '.join(mod_parts)})"
            else:
                return f"Modify: {rule_name}"
        else:
            return f"Unknown: {effect_type}"

    # =================== ALL EXISTING METHODS UPDATED WITH POLYMERASE SUPPORT ===================

    # MILESTONE EVENT HANDLERS
    def on_milestone_select(self, event):
        """Handle milestone selection"""
        selection = self.milestone_listbox.curselection()
        if not selection:
            return

        display_text = self.milestone_listbox.get(selection[0])
        milestone_id = display_text.split(" (")[0]
        self.load_milestone_data(milestone_id)

    def on_milestone_click(self, event):
        """Handle milestone click"""
        self.milestone_listbox.after(10, self.handle_milestone_selection)

    def on_milestone_double_click(self, event):
        """Handle milestone double-click"""
        self.handle_milestone_selection()

    def handle_milestone_selection(self):
        """Common method to handle milestone selection"""
        selection = self.milestone_listbox.curselection()
        if not selection:
            return

        display_text = self.milestone_listbox.get(selection[0])
        milestone_id = display_text.split(" (")[0]
        self.load_milestone_data(milestone_id)

    def on_milestone_type_change(self, event=None):
        """Handle milestone type change to update UI"""
        milestone_type = self.milestone_type_var.get()

        # Update entity class combo availability and values
        if milestone_type in ["peak_entity_count", "cumulative_entity_count"]:
            # Enable entity class selection
            self.milestone_entity_class_combo.config(state="readonly")
            entity_classes = self.db_manager.get_entity_classes()
            self.milestone_entity_class_combo['values'] = entity_classes
            if entity_classes and not self.milestone_entity_class_var.get():
                self.milestone_entity_class_var.set(entity_classes[0])
        else:
            # Disable entity class selection
            self.milestone_entity_class_combo.config(state="disabled")
            self.milestone_entity_class_var.set("")

        # Update help text
        self.update_milestone_help_text(milestone_type)

    def update_milestone_help_text(self, milestone_type):
        """Update help text based on milestone type"""
        help_texts = {
            "survive_turns": "Player must survive for at least the target number of turns in a single play run",
            "peak_entity_count": "Player must have at least the target number of entities of the chosen class present simultaneously",
            "cumulative_entity_count": "Player must create at least the target total number of entities of the chosen class during a single play run"
        }

        help_text = help_texts.get(milestone_type, "Select a milestone type to see instructions")
        self.milestone_help_label.config(text=help_text)

    def load_milestone_data(self, milestone_id):
        """Load milestone data into form"""
        milestone = self.db_manager.get_milestone(milestone_id)
        if not milestone:
            return

        # Store reference for save operations
        self.current_milestone_id = milestone_id

        # Simple status update
        self.milestone_status_label.config(text=f"Selected: {milestone_id}")

        # Load data directly
        self.milestone_id_var.set(milestone.get("id", ""))
        self.milestone_name_var.set(milestone.get("name", ""))

        self.milestone_desc_text.delete(1.0, tk.END)
        self.milestone_desc_text.insert(1.0, milestone.get("description", ""))

        self.milestone_type_var.set(milestone.get("type", "survive_turns"))
        self.milestone_target_var.set(milestone.get("target", 5))
        self.milestone_reward_var.set(milestone.get("reward_ep", 25))
        self.milestone_entity_class_var.set(milestone.get("entity_class", ""))

        # Update UI based on type
        self.on_milestone_type_change()

    # ENTITY EVENT HANDLERS - CLEAN VERSION
    def on_entity_select(self, event):
        """Handle entity selection"""
        selection = self.entity_listbox.curselection()
        if not selection:
            return

        display_text = self.entity_listbox.get(selection[0])

        # Parse entity name correctly - remove only the last parenthetical (degradation rate + starter indicator)
        if " (" in display_text and display_text.endswith(")"):
            last_paren = display_text.rfind(" (")
            entity_name = display_text[:last_paren]
        else:
            entity_name = display_text

        self.load_entity_data(entity_name)

    def on_entity_click(self, event):
        """Handle entity click"""
        # Small delay to let selection register
        self.entity_listbox.after(10, self.handle_entity_selection)

    def on_entity_double_click(self, event):
        """Handle entity double-click"""
        self.handle_entity_selection()

    def handle_entity_selection(self):
        """Common method to handle entity selection"""
        selection = self.entity_listbox.curselection()
        if not selection:
            return

        display_text = self.entity_listbox.get(selection[0])

        # Parse entity name correctly - remove only the last parenthetical (degradation rate + starter indicator)
        if " (" in display_text and display_text.endswith(")"):
            last_paren = display_text.rfind(" (")
            entity_name = display_text[:last_paren]
        else:
            entity_name = display_text

        self.load_entity_data(entity_name)

    def load_entity_data(self, entity_name):
        """Load entity data into form - WITH STARTER SUPPORT"""
        entity = self.db_manager.get_entity(entity_name)
        if not entity:
            return

        # Store reference for save operations
        self.current_entity_name = entity_name

        # Simple status update
        self.entity_status_label.config(text=f"Selected: {entity_name}")

        # Load data directly
        self.entity_name_var.set(entity.get("name", ""))

        self.entity_desc_text.delete(1.0, tk.END)
        self.entity_desc_text.insert(1.0, entity.get("description", ""))

        self.degradation_var.set(entity.get("base_degradation_rate", 0.05))
        self.location_var.set(entity.get("location", ""))
        self.entity_class_var.set(entity.get("entity_class", ""))

        # Load starter status
        self.is_starter_var.set(entity.get("is_starter", False))

    # GENE EVENT HANDLERS - UPDATED WITH POLYMERASE SUPPORT
    def on_gene_select(self, event):
        """Handle gene selection"""
        selection = self.gene_listbox.curselection()
        if not selection:
            return

        display_text = self.gene_listbox.get(selection[0])
        gene_name = display_text.split(" (")[0]
        self.load_gene_data(gene_name)

    def on_gene_click(self, event):
        """Handle gene click"""
        self.gene_listbox.after(10, self.handle_gene_selection)

    def on_gene_double_click(self, event):
        """Handle gene double-click"""
        self.handle_gene_selection()

    def handle_gene_selection(self):
        """Common method to handle gene selection"""
        selection = self.gene_listbox.curselection()
        if not selection:
            return

        display_text = self.gene_listbox.get(selection[0])
        gene_name = display_text.split(" (")[0]
        self.load_gene_data(gene_name)

    def load_gene_data(self, gene_name):
        """Load gene data into form - UPDATED WITH POLYMERASE SUPPORT"""
        gene = self.db_manager.get_gene(gene_name)
        if not gene:
            return

        # Store reference for save operations
        self.current_gene_name = gene_name

        # Simple status update
        self.gene_status_label.config(text=f"Selected: {gene_name}")

        # Load data directly
        self.gene_name_var.set(gene.get("name", ""))
        self.gene_cost_var.set(gene.get("cost", 0))

        self.gene_desc_text.delete(1.0, tk.END)
        self.gene_desc_text.insert(1.0, gene.get("description", ""))

        # Load prerequisites
        self.prereq_listbox.delete(0, tk.END)
        for req in gene.get("requires", []):
            self.prereq_listbox.insert(tk.END, req)

        # Load effects
        self.effects_listbox.delete(0, tk.END)
        for effect in gene.get("effects", []):
            effect_desc = self.format_effect_description(effect)
            self.effects_listbox.insert(tk.END, effect_desc)

        # NEW: Load polymerase status
        self.is_polymerase_var.set(gene.get("is_polymerase", False))

    def update_entity_list(self):
        """Update the entity list - UPDATED TO SHOW STARTER STATUS"""
        self.entity_listbox.delete(0, tk.END)

        for entity_name in sorted(self.db_manager.get_all_entity_names()):
            entity = self.db_manager.get_entity(entity_name)
            degradation = entity.get("base_degradation_rate", 0.05)
            is_starter = entity.get("is_starter", False)

            # Format: "Entity Name (degradation, starter)" or "Entity Name (degradation)"
            if is_starter:
                display_text = f"{entity_name} ({degradation:.2f}, starter)"
            else:
                display_text = f"{entity_name} ({degradation:.2f})"

            self.entity_listbox.insert(tk.END, display_text)

    def update_gene_list(self):
        """Update the gene list - UPDATED TO SHOW POLYMERASE STATUS"""
        self.gene_listbox.delete(0, tk.END)

        for gene_name in sorted(self.db_manager.get_all_genes()):
            gene = self.db_manager.get_gene(gene_name)
            cost = gene.get("cost", 0)
            is_polymerase = gene.get("is_polymerase", False)

            # Format: "Gene Name (cost EP, Polymerase)" or "Gene Name (cost EP)"
            if is_polymerase:
                display_text = f"{gene_name} ({cost} EP, Polymerase)"
            else:
                display_text = f"{gene_name} ({cost} EP)"

            self.gene_listbox.insert(tk.END, display_text)

    # MILESTONE CRUD METHODS
    def save_milestone(self):
        """Save current milestone"""
        # Build milestone data from form
        milestone_data = {
            "id": self.milestone_id_var.get().strip(),
            "name": self.milestone_name_var.get().strip(),
            "description": self.milestone_desc_text.get(1.0, tk.END).strip(),
            "type": self.milestone_type_var.get(),
            "target": self.milestone_target_var.get(),
            "reward_ep": self.milestone_reward_var.get()
        }

        # Add entity_class if applicable
        if milestone_data["type"] in ["peak_entity_count", "cumulative_entity_count"]:
            milestone_data["entity_class"] = self.milestone_entity_class_var.get()

        # Validate
        is_valid, error_msg = self.db_manager.validate_milestone_data(milestone_data)
        if not is_valid:
            messagebox.showerror("Validation Error", error_msg)
            return

        # Handle ID changes
        old_id = getattr(self, 'current_milestone_id', None)
        new_id = milestone_data["id"]

        if old_id and old_id != new_id:
            self.db_manager.delete_milestone(old_id)

        # Save
        self.db_manager.add_milestone(milestone_data)
        self.current_milestone_id = new_id

        # Update displays
        self.update_milestone_list()
        self.update_database_display()
        self.milestone_status_label.config(text=f"Selected: {new_id} (Saved)")

        # Notify controller of database change
        if hasattr(self.controller, 'handle_database_change'):
            self.controller.handle_database_change()

        messagebox.showinfo("Success", f"Milestone '{new_id}' saved")

    def save_milestone_as_new(self):
        """Save as new milestone"""
        # Clear current selection and save
        self.current_milestone_id = None
        self.milestone_status_label.config(text="Creating new milestone")
        self.save_milestone()

    def clear_milestone_form(self):
        """Clear the milestone form"""
        self.current_milestone_id = None
        self.milestone_status_label.config(text="No milestone selected")
        self.milestone_id_var.set("")
        self.milestone_name_var.set("")
        self.milestone_desc_text.delete(1.0, tk.END)
        self.milestone_type_var.set("survive_turns")
        self.milestone_target_var.set(5)
        self.milestone_reward_var.set(25)
        self.milestone_entity_class_var.set("")
        self.on_milestone_type_change()

    def new_milestone(self):
        """Create a new milestone"""
        self.clear_milestone_form()
        self.milestone_id_var.set("new_milestone")
        self.milestone_name_var.set("New Milestone")
        self.milestone_type_var.set("survive_turns")
        self.milestone_target_var.set(5)
        self.milestone_reward_var.set(25)
        self.milestone_status_label.config(text="Creating new milestone")
        self.on_milestone_type_change()

    def clone_milestone(self):
        """Clone the selected milestone"""
        if not hasattr(self, 'current_milestone_id') or not self.current_milestone_id:
            messagebox.showwarning("No Milestone", "Please select a milestone to clone")
            return

        # Get current form data and modify ID
        current_id = self.milestone_id_var.get()
        self.milestone_id_var.set(f"{current_id}_copy")
        self.current_milestone_id = None  # Clear so it saves as new
        self.milestone_status_label.config(text="Cloning milestone")

    def delete_milestone(self):
        """Delete the selected milestone"""
        if not hasattr(self, 'current_milestone_id') or not self.current_milestone_id:
            messagebox.showwarning("No Selection", "Please select a milestone to delete")
            return

        milestone_id = self.current_milestone_id

        if messagebox.askyesno("Confirm Delete", f"Delete milestone '{milestone_id}'?"):
            self.db_manager.delete_milestone(milestone_id)
            self.update_milestone_list()
            self.update_database_display()
            self.clear_milestone_form()

            # Notify controller of database change
            if hasattr(self.controller, 'handle_database_change'):
                self.controller.handle_database_change()

    def update_milestone_list(self):
        """Update the milestone list"""
        self.milestone_listbox.delete(0, tk.END)

        for milestone_id in sorted(self.db_manager.get_all_milestones()):
            milestone = self.db_manager.get_milestone(milestone_id)
            reward = milestone.get("reward_ep", 0)
            milestone_type = milestone.get("type", "unknown")
            target = milestone.get("target", 0)

            # Format display text based on type
            if milestone_type == "survive_turns":
                display_text = f"{milestone_id} ({target} turns, {reward} EP)"
            elif milestone_type in ["peak_entity_count", "cumulative_entity_count"]:
                entity_class = milestone.get("entity_class", "unknown")
                type_short = "peak" if milestone_type == "peak_entity_count" else "total"
                display_text = f"{milestone_id} ({target} {entity_class} {type_short}, {reward} EP)"
            else:
                display_text = f"{milestone_id} ({reward} EP)"

            self.milestone_listbox.insert(tk.END, display_text)

    # ENTITY CRUD METHODS - WITH STARTER SUPPORT
    def save_entity(self):
        """Save current entity - WITH STARTER SUPPORT"""
        # Build entity data from form
        entity_data = {
            "name": self.entity_name_var.get().strip(),
            "description": self.entity_desc_text.get(1.0, tk.END).strip(),
            "base_degradation_rate": self.degradation_var.get(),
            "location": self.location_var.get(),
            "entity_class": self.entity_class_var.get(),
            "is_starter": self.is_starter_var.get()  # Include starter status
        }

        # Validate
        if not entity_data["name"]:
            messagebox.showerror("Error", "Entity name cannot be empty")
            return

        if entity_data["base_degradation_rate"] < 0 or entity_data["base_degradation_rate"] > 1:
            messagebox.showerror("Error", "Degradation rate must be between 0.0 and 1.0")
            return

        # Handle name changes
        old_name = getattr(self, 'current_entity_name', None)
        new_name = entity_data["name"]

        if old_name and old_name != new_name:
            self.db_manager.delete_entity(old_name)

        # Save
        self.db_manager.add_entity(entity_data)
        self.current_entity_name = new_name

        # Update displays
        self.update_entity_list()
        self.update_milestone_list()  # Entity class changes may affect milestones
        self.update_database_display()
        self.entity_status_label.config(text=f"Selected: {new_name} (Saved)")

        messagebox.showinfo("Success", f"Entity '{new_name}' saved")

    def save_entity_as_new(self):
        """Save as new entity"""
        # Clear current selection and save
        self.current_entity_name = None
        self.entity_status_label.config(text="Creating new entity")
        self.save_entity()

    def clear_entity_form(self):
        """Clear the entity form - WITH STARTER SUPPORT"""
        self.current_entity_name = None
        self.entity_status_label.config(text="No entity selected")
        self.entity_name_var.set("")
        self.entity_desc_text.delete(1.0, tk.END)
        self.degradation_var.set(0.05)
        self.location_var.set("")
        self.entity_class_var.set("")
        self.is_starter_var.set(False)  # Reset starter checkbox

    def new_entity(self):
        """Create a new entity - WITH STARTER SUPPORT"""
        self.clear_entity_form()
        self.entity_name_var.set("New Entity")
        self.degradation_var.set(0.05)
        self.location_var.set("unknown")
        self.entity_class_var.set("unknown")
        self.is_starter_var.set(False)  # Default to non-starter
        self.entity_status_label.config(text="Creating new entity")

    def clone_entity(self):
        """Clone the selected entity"""
        if not hasattr(self, 'current_entity_name') or not self.current_entity_name:
            messagebox.showwarning("No Entity", "Please select an entity to clone")
            return

        # Get current form data and modify name
        current_name = self.entity_name_var.get()
        self.entity_name_var.set(f"{current_name} (Copy)")
        self.current_entity_name = None  # Clear so it saves as new
        self.entity_status_label.config(text="Cloning entity")

    def delete_entity(self):
        """Delete the selected entity"""
        if not hasattr(self, 'current_entity_name') or not self.current_entity_name:
            messagebox.showwarning("No Selection", "Please select an entity to delete")
            return

        entity_name = self.current_entity_name

        # Check if entity is used in genes
        used_in_genes = []
        for gene_name, gene_data in self.db_manager.database["genes"].items():
            for effect in gene_data.get("effects", []):
                if (effect["type"] == "enable_entity" and effect.get("entity") == entity_name) or \
                        (effect["type"] in ["add_transition"]):
                    rule = effect.get("rule", {})
                    for input_spec in rule.get("inputs", []):
                        if input_spec["entity"] == entity_name:
                            used_in_genes.append(gene_name)
                            break
                    for output_spec in rule.get("outputs", []):
                        if output_spec["entity"] == entity_name:
                            used_in_genes.append(gene_name)
                            break

        if used_in_genes:
            messagebox.showerror("Cannot Delete",
                                 f"Entity '{entity_name}' is used in genes: {', '.join(set(used_in_genes))}\n"
                                 f"Remove it from these genes first.")
            return

        if messagebox.askyesno("Confirm Delete", f"Delete entity '{entity_name}'?"):
            self.db_manager.delete_entity(entity_name)
            self.update_entity_list()
            self.update_milestone_list()  # Update milestones display
            self.update_database_display()
            self.clear_entity_form()

    # GENE CRUD METHODS - UPDATED WITH POLYMERASE SUPPORT
    def save_gene(self):
        """Save current gene - UPDATED WITH POLYMERASE SUPPORT"""
        # Build gene data from form
        gene_data = {
            "name": self.gene_name_var.get().strip(),
            "cost": self.gene_cost_var.get(),
            "description": self.gene_desc_text.get(1.0, tk.END).strip(),
            "effects": [],
            "is_polymerase": self.is_polymerase_var.get()  # NEW: Include polymerase status
        }

        # Validate
        if not gene_data["name"]:
            messagebox.showerror("Error", "Gene name cannot be empty")
            return

        # Add prerequisites if any
        prereqs = []
        for i in range(self.prereq_listbox.size()):
            prereqs.append(self.prereq_listbox.get(i))
        if prereqs:
            gene_data["requires"] = prereqs

        # Get current gene data to preserve effects
        if hasattr(self, 'current_gene_name') and self.current_gene_name:
            current_gene = self.db_manager.get_gene(self.current_gene_name)
            if current_gene:
                gene_data["effects"] = current_gene.get("effects", [])

        # Handle name changes
        old_name = getattr(self, 'current_gene_name', None)
        new_name = gene_data["name"]

        if old_name and old_name != new_name:
            self.db_manager.delete_gene(old_name)

        # Save
        self.db_manager.add_gene(gene_data)
        self.current_gene_name = new_name

        # Update displays
        self.update_gene_list()
        self.update_database_display()
        self.gene_status_label.config(text=f"Selected: {new_name} (Saved)")

        messagebox.showinfo("Success", f"Gene '{new_name}' saved")

    def save_gene_as_new(self):
        """Save as new gene"""
        # Clear current selection and save
        self.current_gene_name = None
        self.gene_status_label.config(text="Creating new gene")
        self.save_gene()

    def clear_gene_form(self):
        """Clear the gene form - UPDATED WITH POLYMERASE SUPPORT"""
        self.current_gene_name = None
        self.gene_status_label.config(text="No gene selected")
        self.gene_name_var.set("")
        self.gene_cost_var.set(0)
        self.gene_desc_text.delete(1.0, tk.END)
        self.prereq_listbox.delete(0, tk.END)
        self.effects_listbox.delete(0, tk.END)
        self.is_polymerase_var.set(False)  # NEW: Reset polymerase checkbox

    def new_gene(self):
        """Create a new gene - UPDATED WITH POLYMERASE SUPPORT"""
        self.clear_gene_form()
        self.gene_name_var.set("New Gene")
        self.gene_cost_var.set(0)
        self.is_polymerase_var.set(False)  # NEW: Default to non-polymerase
        self.gene_status_label.config(text="Creating new gene")

    def clone_gene(self):
        """Clone the selected gene"""
        if not hasattr(self, 'current_gene_name') or not self.current_gene_name:
            messagebox.showwarning("No Gene", "Please select a gene to clone")
            return

        # Get current form data and modify name
        current_name = self.gene_name_var.get()
        self.gene_name_var.set(f"{current_name} (Copy)")
        self.current_gene_name = None  # Clear so it saves as new
        self.gene_status_label.config(text="Cloning gene")

    def delete_gene(self):
        """Delete the selected gene"""
        if not hasattr(self, 'current_gene_name') or not self.current_gene_name:
            messagebox.showwarning("No Selection", "Please select a gene to delete")
            return

        gene_name = self.current_gene_name

        if messagebox.askyesno("Confirm Delete", f"Delete gene '{gene_name}'?"):
            self.db_manager.delete_gene(gene_name)
            self.update_gene_list()
            self.update_database_display()
            self.clear_gene_form()

    def add_prerequisite(self):
        """Add prerequisite gene"""
        # Get available genes
        available_genes = [name for name in self.db_manager.get_all_genes()
                           if name != self.gene_name_var.get()]

        if not available_genes:
            messagebox.showinfo("No Genes", "No other genes available as prerequisites")
            return

        # Simple selection dialog
        prereq = simpledialog.askstring("Add Prerequisite",
                                        f"Available genes: {', '.join(available_genes)}\n\nEnter prerequisite gene name:")
        if prereq and prereq in available_genes:
            # Check if already in list
            current_prereqs = [self.prereq_listbox.get(i) for i in range(self.prereq_listbox.size())]
            if prereq not in current_prereqs:
                self.prereq_listbox.insert(tk.END, prereq)
            else:
                messagebox.showinfo("Already Added", f"'{prereq}' is already a prerequisite")
        elif prereq:
            messagebox.showerror("Invalid Gene", f"'{prereq}' is not a valid gene name")

    def remove_prerequisite(self):
        """Remove prerequisite gene"""
        selection = self.prereq_listbox.curselection()
        if selection:
            self.prereq_listbox.delete(selection[0])

    def add_effect(self):
        """Add new effect"""
        self.open_effect_editor(None)

    def edit_effect(self):
        """Edit selected effect"""
        selection = self.effects_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an effect to edit")
            return

        effect_index = selection[0]
        if hasattr(self, 'current_gene_name') and self.current_gene_name:
            gene = self.db_manager.get_gene(self.current_gene_name)
            if gene and effect_index < len(gene.get("effects", [])):
                effect = gene["effects"][effect_index]
                self.open_effect_editor(effect, effect_index)

    def remove_effect(self):
        """Remove selected effect"""
        selection = self.effects_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an effect to remove")
            return

        if not hasattr(self, 'current_gene_name') or not self.current_gene_name:
            messagebox.showwarning("No Gene", "No gene selected")
            return

        effect_index = selection[0]
        gene = self.db_manager.get_gene(self.current_gene_name)
        if gene and effect_index < len(gene.get("effects", [])):
            # Remove effect and update gene
            gene_effects = gene.get("effects", [])
            del gene_effects[effect_index]

            # Update gene in database
            updated_gene = gene.copy()
            updated_gene["effects"] = gene_effects
            self.db_manager.add_gene(updated_gene)

            # Refresh effects display
            self.load_gene_data(self.current_gene_name)

    def on_effect_select(self, event):
        """Handle effect selection"""
        pass  # Could show effect details

    def open_effect_editor(self, effect=None, effect_index=None):
        """Open effect editor dialog"""
        dialog = EffectEditorDialog(self.frame, effect, self.db_manager.get_all_entity_names())
        self.frame.wait_window(dialog.dialog)

        if dialog.result and hasattr(self, 'current_gene_name') and self.current_gene_name:
            # Get current gene
            gene = self.db_manager.get_gene(self.current_gene_name)
            if not gene:
                return

            # Update effects
            effects = gene.get("effects", [])

            if effect_index is not None:
                # Update existing effect
                effects[effect_index] = dialog.result
            else:
                # Add new effect
                effects.append(dialog.result)

            # Update gene in database
            updated_gene = gene.copy()
            updated_gene["effects"] = effects
            self.db_manager.add_gene(updated_gene)

            # Refresh display
            self.load_gene_data(self.current_gene_name)

    # DATABASE METHODS - UPDATED WITH MILESTONE COUNT
    def new_database(self):
        """Create a new database"""
        if self.db_manager.is_modified:
            result = messagebox.askyesnocancel("Unsaved Changes", "Save changes before creating new database?")
            if result is True:
                self.save_database()
            elif result is None:
                return

        self.db_manager = GeneDatabaseManager()
        self.update_database_display()
        self.update_entity_list()
        self.update_gene_list()
        self.update_milestone_list()
        self.clear_entity_form()
        self.clear_gene_form()
        self.clear_milestone_form()

    def open_database(self):
        """Open database file"""
        if self.db_manager.is_modified:
            result = messagebox.askyesnocancel("Unsaved Changes", "Save changes before opening?")
            if result is True:
                self.save_database()
            elif result is None:
                return

        file_path = filedialog.askopenfilename(
            title="Open Gene Database",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )

        if file_path:
            try:
                self.db_manager.load_database(file_path)
                self.update_database_display()
                self.update_entity_list()
                self.update_gene_list()
                self.update_milestone_list()
                self.clear_entity_form()
                self.clear_gene_form()
                self.clear_milestone_form()

                # Notify controller of database change
                if hasattr(self.controller, 'handle_database_change'):
                    self.controller.handle_database_change()

                messagebox.showinfo("Success",
                                    f"Loaded database with {len(self.db_manager.get_all_genes())} genes, "
                                    f"{len(self.db_manager.get_all_entity_names())} entities, and "
                                    f"{len(self.db_manager.get_all_milestones())} milestones")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load database:\n{e}")

    def save_database(self):
        """Save current database"""
        if not self.db_manager.file_path:
            self.save_as_database()
            return

        try:
            # Update database info from UI
            self.update_database_info_from_ui()
            self.db_manager.save_database()
            self.update_database_display()

            # Notify controller of database change
            if hasattr(self.controller, 'handle_database_change'):
                self.controller.handle_database_change()

            messagebox.showinfo("Success", "Database saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save database:\n{e}")

    def save_as_database(self):
        """Save database as new file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Gene Database As",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json",
            initialdir=os.getcwd()
        )

        if file_path:
            try:
                # Update database info from UI
                self.update_database_info_from_ui()
                self.db_manager.save_database(file_path)
                self.update_database_display()

                # Notify controller of database change
                if hasattr(self.controller, 'handle_database_change'):
                    self.controller.handle_database_change()

                messagebox.showinfo("Success", f"Database saved as {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save database:\n{e}")

    def update_database_display(self):
        """Update database info display - WITH MILESTONE COUNT"""
        db_info = self.db_manager.database["database_info"]

        self.db_name_var.set(db_info.get("name", ""))
        self.db_version_var.set(db_info.get("version", ""))

        self.db_desc_text.delete(1.0, tk.END)
        self.db_desc_text.insert(1.0, db_info.get("description", ""))

        # Status - updated to show milestone count
        if self.db_manager.file_path:
            filename = os.path.basename(self.db_manager.file_path)
            gene_count = len(self.db_manager.get_all_genes())
            entity_count = len(self.db_manager.get_all_entity_names())
            starter_count = len(self.db_manager.get_starter_entities())
            milestone_count = len(self.db_manager.get_all_milestones())
            polymerase_count = len(self.db_manager.get_polymerase_genes())  # NEW: Show polymerase count
            modified = " *" if self.db_manager.is_modified else ""
            self.status_label.config(
                text=f"File: {filename} | {gene_count} genes ({polymerase_count} polymerase), {entity_count} entities "
                     f"({starter_count} starters), {milestone_count} milestones{modified}")
        else:
            gene_count = len(self.db_manager.get_all_genes())
            entity_count = len(self.db_manager.get_all_entity_names())
            starter_count = len(self.db_manager.get_starter_entities())
            milestone_count = len(self.db_manager.get_all_milestones())
            polymerase_count = len(self.db_manager.get_polymerase_genes())  # NEW: Show polymerase count
            modified = " *" if self.db_manager.is_modified else ""
            self.status_label.config(
                text=f"New database | {gene_count} genes ({polymerase_count} polymerase), {entity_count} entities "
                     f"({starter_count} starters), {milestone_count} milestones{modified}")

    def update_database_info_from_ui(self):
        """Update database info from UI fields"""
        db_info = self.db_manager.database["database_info"]
        db_info["name"] = self.db_name_var.get()
        db_info["version"] = self.db_version_var.get()
        db_info["description"] = self.db_desc_text.get(1.0, tk.END).strip()


class EffectEditorDialog:
    """Dialog for editing gene effects - UPDATED TO SUPPORT INTERFERON EFFECTS"""

    def __init__(self, parent, effect=None, available_entities=None):
        self.result = None
        self.available_entities = available_entities or []

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Effect Editor")
        self.dialog.geometry("700x650")  # Increased height for interferon fields
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (650 // 2)
        self.dialog.geometry(f"700x650+{x}+{y}")

        self.setup_ui(effect)

    def setup_ui(self, effect):
        """Setup the effect editor UI"""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(header_frame, text="Edit Gene Effect", font=("Arial", 14, "bold")).pack()

        # Effect type selection
        type_frame = ttk.LabelFrame(self.dialog, text="Effect Type", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.effect_type_var = tk.StringVar()
        self.effect_type_var.trace('w', self.on_effect_type_change)

        effect_types = [
            ("add_transition", "Add Transition"),
            ("modify_transition", "Modify Transition")
        ]

        for i, (value, text) in enumerate(effect_types):
            ttk.Radiobutton(type_frame, text=text, variable=self.effect_type_var,
                            value=value).grid(row=0, column=i, padx=10, sticky=tk.W)

        # Dynamic content area
        self.content_frame = ttk.Frame(self.dialog)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.RIGHT)

        # Initialize with effect data if provided
        if effect:
            self.load_effect(effect)
        else:
            self.effect_type_var.set("add_transition")

    def load_effect(self, effect):
        """Load existing effect data"""
        effect_type = effect.get("type", "add_transition")
        self.effect_type_var.set(effect_type)

        # The UI will be updated by the trace callback
        self.dialog.after(100, lambda: self.populate_fields(effect))

    def populate_fields(self, effect):
        """Populate fields with effect data - UPDATED FOR INTERFERON SUPPORT"""
        effect_type = effect.get("type", "add_transition")

        if effect_type == "add_transition":
            rule = effect.get("rule", {})
            if hasattr(self, 'rule_name_var'):
                self.rule_name_var.set(rule.get("name", ""))
                self.probability_var.set(int(rule.get("probability", 0.5) * 100))
                self.rule_type_var.set(rule.get("rule_type", "per_entity"))

                # Load inputs (up to 3)
                inputs = rule.get("inputs", [])
                for i in range(3):
                    if i < len(inputs):
                        input_data = inputs[i]
                        self.input_entity_vars[i].set(input_data["entity"])
                        self.input_count_vars[i].set(input_data["count"])
                        # Set consumed status from first input (since it's all-or-nothing)
                        if i == 0:
                            self.input_consumed_var.set(input_data.get("consumed", True))
                    else:
                        # Clear unused input fields
                        self.input_entity_vars[i].set("")
                        self.input_count_vars[i].set(1)

                # Load outputs (up to 3)
                outputs = rule.get("outputs", [])
                for i in range(3):
                    if i < len(outputs):
                        output_data = outputs[i]
                        self.output_entity_vars[i].set(output_data["entity"])
                        self.output_count_vars[i].set(output_data["count"])
                    else:
                        # Clear unused output fields
                        self.output_entity_vars[i].set("")
                        self.output_count_vars[i].set(1)

                # NEW: Load interferon data
                interferon_amount = rule.get("interferon_amount", 0.0)
                if interferon_amount > 0:
                    self.interferon_enabled_var.set(True)
                    self.interferon_amount_var.set(interferon_amount)
                else:
                    self.interferon_enabled_var.set(False)
                    self.interferon_amount_var.set(0.0)

        elif effect_type == "modify_transition":
            if hasattr(self, 'modify_rule_var'):
                self.modify_rule_var.set(effect.get("rule_name", ""))
                modification = effect.get("modification", {})

                # Load probability multiplier
                prob_mult = modification.get("probability_multiplier", 1.0)
                self.probability_multiplier_var.set(prob_mult)

                # NEW: Load interferon multiplier
                interferon_mult = modification.get("interferon_multiplier", 1.0)
                self.interferon_multiplier_var.set(interferon_mult)

    def on_effect_type_change(self, *args):
        """Handle effect type change"""
        # Clear current content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        effect_type = self.effect_type_var.get()

        if effect_type == "add_transition":
            self.setup_add_transition_ui()
        elif effect_type == "modify_transition":
            self.setup_modify_transition_ui()

    def setup_add_transition_ui(self):
        """Setup UI for add transition effect - UPDATED FOR INTERFERON SUPPORT"""
        # Create scrollable frame for the content
        canvas = tk.Canvas(self.content_frame)
        scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Main frame for rule content
        frame = ttk.LabelFrame(scrollable_frame, text="Add Transition Rule", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        current_row = 0

        # Rule name
        ttk.Label(frame, text="Rule Name:").grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10))
        self.rule_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.rule_name_var, width=30).grid(row=current_row, column=1, columnspan=2,
                                                                         sticky=tk.W)
        current_row += 1

        # Probability
        ttk.Label(frame, text="Probability:").grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.probability_var = tk.IntVar(value=50)
        prob_frame = ttk.Frame(frame)
        prob_frame.grid(row=current_row, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))

        ttk.Scale(prob_frame, from_=0, to=100, variable=self.probability_var, orient=tk.HORIZONTAL, length=150).pack(
            side=tk.LEFT)
        prob_label = ttk.Label(prob_frame, text="50%")
        prob_label.pack(side=tk.LEFT, padx=(5, 0))

        def update_prob_label(*args):
            prob_label.config(text=f"{self.probability_var.get()}%")

        self.probability_var.trace('w', update_prob_label)
        current_row += 1

        # Rule type
        ttk.Label(frame, text="Rule Type:").grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.rule_type_var = tk.StringVar(value="per_entity")
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=current_row, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))

        ttk.Radiobutton(type_frame, text="Per Entity", variable=self.rule_type_var, value="per_entity").pack(
            side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(type_frame, text="Per Pair", variable=self.rule_type_var, value="per_pair").pack(side=tk.LEFT)
        current_row += 1

        # Separator
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=current_row, column=0, columnspan=4, sticky="ew", pady=15)
        current_row += 1

        # INPUT ENTITIES SECTION
        ttk.Label(frame, text="INPUT ENTITIES (up to 3):", font=("Arial", 10, "bold")).grid(
            row=current_row, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))
        current_row += 1

        # Headers for input section
        ttk.Label(frame, text="Entity", font=("Arial", 9, "bold")).grid(row=current_row, column=0, sticky=tk.W,
                                                                        padx=(0, 10))
        ttk.Label(frame, text="Count", font=("Arial", 9, "bold")).grid(row=current_row, column=1, sticky=tk.W,
                                                                       padx=(0, 10))
        ttk.Label(frame, text="Notes", font=("Arial", 9, "bold")).grid(row=current_row, column=2, sticky=tk.W)
        current_row += 1

        # Create 3 input entity rows
        self.input_entity_vars = []
        self.input_count_vars = []

        for i in range(3):
            # Entity dropdown
            input_entity_var = tk.StringVar()
            self.input_entity_vars.append(input_entity_var)
            input_combo = ttk.Combobox(frame, textvariable=input_entity_var, values=self.available_entities, width=25)
            input_combo.grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10), pady=2)

            # Count entry
            input_count_var = tk.IntVar(value=1)
            self.input_count_vars.append(input_count_var)
            ttk.Entry(frame, textvariable=input_count_var, width=8).grid(row=current_row, column=1, sticky=tk.W,
                                                                         padx=(0, 10), pady=2)

            # Notes for first row only
            if i == 0:
                ttk.Label(frame, text="(Leave entity blank to skip row)", font=("Arial", 8, "italic"),
                          foreground="gray").grid(
                    row=current_row, column=2, sticky=tk.W, pady=2)

            current_row += 1

        # Consumed checkbox (applies to all inputs)
        self.input_consumed_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="All input entities are consumed when transition fires",
                        variable=self.input_consumed_var).grid(row=current_row, column=0, columnspan=3, sticky=tk.W,
                                                               pady=(5, 15))
        current_row += 1

        # Separator
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=current_row, column=0, columnspan=4, sticky="ew", pady=15)
        current_row += 1

        # OUTPUT ENTITIES SECTION
        ttk.Label(frame, text="OUTPUT ENTITIES (up to 3):", font=("Arial", 10, "bold")).grid(
            row=current_row, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))
        current_row += 1

        # Headers for output section
        ttk.Label(frame, text="Entity", font=("Arial", 9, "bold")).grid(row=current_row, column=0, sticky=tk.W,
                                                                        padx=(0, 10))
        ttk.Label(frame, text="Count", font=("Arial", 9, "bold")).grid(row=current_row, column=1, sticky=tk.W,
                                                                       padx=(0, 10))
        ttk.Label(frame, text="Notes", font=("Arial", 9, "bold")).grid(row=current_row, column=2, sticky=tk.W)
        current_row += 1

        # Create 3 output entity rows
        self.output_entity_vars = []
        self.output_count_vars = []

        for i in range(3):
            # Entity dropdown
            output_entity_var = tk.StringVar()
            self.output_entity_vars.append(output_entity_var)
            output_combo = ttk.Combobox(frame, textvariable=output_entity_var, values=self.available_entities, width=25)
            output_combo.grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10), pady=2)

            # Count entry
            output_count_var = tk.IntVar(value=1)
            self.output_count_vars.append(output_count_var)
            ttk.Entry(frame, textvariable=output_count_var, width=8).grid(row=current_row, column=1, sticky=tk.W,
                                                                          padx=(0, 10), pady=2)

            # Notes for first row only
            if i == 0:
                ttk.Label(frame, text="(Leave entity blank to skip row)", font=("Arial", 8, "italic"),
                          foreground="gray").grid(
                    row=current_row, column=2, sticky=tk.W, pady=2)

            current_row += 1

        # NEW: INTERFERON SECTION
        # Separator
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=current_row, column=0, columnspan=4, sticky="ew", pady=15)
        current_row += 1

        # Interferon header
        ttk.Label(frame, text="INTERFERON RESPONSE:", font=("Arial", 10, "bold")).grid(
            row=current_row, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))
        current_row += 1

        # Interferon enable checkbox
        self.interferon_enabled_var = tk.BooleanVar(value=False)
        interferon_checkbox = ttk.Checkbutton(frame, text="This transition triggers interferon response",
                                              variable=self.interferon_enabled_var,
                                              command=self.on_interferon_enabled_change)
        interferon_checkbox.grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        current_row += 1

        # Interferon amount (initially disabled)
        ttk.Label(frame, text="Interferon amount per application:", font=("Arial", 9)).grid(
            row=current_row, column=0, sticky=tk.W, padx=(20, 10), pady=(0, 5))

        interferon_amount_frame = ttk.Frame(frame)
        interferon_amount_frame.grid(row=current_row, column=1, columnspan=2, sticky=tk.W, pady=(0, 5))

        self.interferon_amount_var = tk.DoubleVar(value=1.0)
        self.interferon_amount_entry = ttk.Entry(interferon_amount_frame, textvariable=self.interferon_amount_var,
                                                 width=10)
        self.interferon_amount_entry.pack(side=tk.LEFT)

        ttk.Label(interferon_amount_frame, text="(0.0 - 100.0)", font=("Arial", 8, "italic"), foreground="gray").pack(
            side=tk.LEFT, padx=(5, 0))
        current_row += 1

        # Interferon help text
        self.interferon_help_label = ttk.Label(frame,
                                               text="Each time this transition successfully fires, the specified amount of interferon will be added to the simulation",
                                               font=("Arial", 8, "italic"), foreground="gray", wraplength=400)
        self.interferon_help_label.grid(row=current_row, column=0, columnspan=4, sticky=tk.W, padx=(20, 0),
                                        pady=(0, 10))
        current_row += 1

        # Initially disable interferon fields
        self.on_interferon_enabled_change()

        # Add some padding at bottom
        ttk.Label(frame, text="").grid(row=current_row, column=0, pady=10)

        # Configure canvas scrolling with mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Linux

        # Set focus to the scrollable area so mouse wheel works
        canvas.focus_set()

    def on_interferon_enabled_change(self):
        """Handle interferon enabled checkbox change"""
        enabled = self.interferon_enabled_var.get()

        # Enable/disable interferon amount entry
        if hasattr(self, 'interferon_amount_entry'):
            self.interferon_amount_entry.config(state='normal' if enabled else 'disabled')

        # Update help text color
        if hasattr(self, 'interferon_help_label'):
            color = "gray" if enabled else "#d1d5db"  # lighter gray when disabled
            self.interferon_help_label.config(foreground=color)

    def setup_modify_transition_ui(self):
        """Setup UI for modify transition effect - UPDATED WITH INTERFERON MULTIPLIER"""
        frame = ttk.LabelFrame(self.content_frame, text="Modify Transition Rule", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Rule to modify
        ttk.Label(frame, text="Rule Name to Modify:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.modify_rule_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.modify_rule_var, width=40).grid(row=0, column=1, columnspan=2, sticky=tk.W)

        # Probability multiplier
        ttk.Label(frame, text="Probability Multiplier:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(15, 0))
        self.probability_multiplier_var = tk.DoubleVar(value=1.0)
        ttk.Entry(frame, textvariable=self.probability_multiplier_var, width=10).grid(row=1, column=1, sticky=tk.W,
                                                                                      pady=(15, 0))

        ttk.Label(frame, text="(1.0 = no change, 1.5 = 50% increase, 0.5 = 50% decrease)",
                  font=("Arial", 9, "italic")).grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # NEW: Interferon multiplier
        ttk.Label(frame, text="Interferon Multiplier:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(15, 0))
        self.interferon_multiplier_var = tk.DoubleVar(value=1.0)
        ttk.Entry(frame, textvariable=self.interferon_multiplier_var, width=10).grid(row=3, column=1, sticky=tk.W,
                                                                                     pady=(15, 0))

        ttk.Label(frame, text="(1.0 = no change, 2.0 = double interferon, 0.0 = disable interferon)",
                  font=("Arial", 9, "italic")).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # Additional help
        ttk.Label(frame, text="Note: Interferon multiplier only affects transitions that already produce interferon",
                  font=("Arial", 9, "italic"), foreground="#dc2626").grid(row=5, column=0, columnspan=3, sticky=tk.W,
                                                                          pady=(10, 0))

    def ok_clicked(self):
        """Handle OK button click - UPDATED FOR INTERFERON SUPPORT"""
        effect_type = self.effect_type_var.get()

        try:
            if effect_type == "add_transition":
                rule_name = self.rule_name_var.get().strip()
                if not rule_name:
                    messagebox.showerror("Error", "Rule name is required")
                    return

                # Build inputs list (filter out empty entities)
                inputs = []
                for i in range(3):
                    entity_name = self.input_entity_vars[i].get().strip()
                    if entity_name:  # Only add if entity is specified
                        count = self.input_count_vars[i].get()
                        if count <= 0:
                            messagebox.showerror("Error", f"Input {i + 1} count must be greater than 0")
                            return
                        inputs.append({
                            "entity": entity_name,
                            "count": count,
                            "consumed": self.input_consumed_var.get()
                        })

                # Build outputs list (filter out empty entities)
                outputs = []
                for i in range(3):
                    entity_name = self.output_entity_vars[i].get().strip()
                    if entity_name:  # Only add if entity is specified
                        count = self.output_count_vars[i].get()
                        if count <= 0:
                            messagebox.showerror("Error", f"Output {i + 1} count must be greater than 0")
                            return
                        outputs.append({
                            "entity": entity_name,
                            "count": count
                        })

                # Validate that we have at least one input
                if not inputs:
                    messagebox.showerror("Error", "At least one input entity is required")
                    return

                # Build rule object
                rule_data = {
                    "name": rule_name,
                    "inputs": inputs,
                    "outputs": outputs,
                    "probability": self.probability_var.get() / 100.0,
                    "rule_type": self.rule_type_var.get()
                }

                # NEW: Add interferon amount if enabled
                if self.interferon_enabled_var.get():
                    interferon_amount = self.interferon_amount_var.get()

                    # Validate interferon amount
                    if interferon_amount < 0.0 or interferon_amount > 100.0:
                        messagebox.showerror("Error", "Interferon amount must be between 0.0 and 100.0")
                        return

                    if interferon_amount > 0.0:  # Only add if actually specified
                        rule_data["interferon_amount"] = round(interferon_amount, 2)

                self.result = {
                    "type": effect_type,
                    "rule": rule_data
                }

            elif effect_type == "modify_transition":
                rule_name = self.modify_rule_var.get().strip()
                if not rule_name:
                    messagebox.showerror("Error", "Rule name is required")
                    return

                # Build modification object
                modification = {}

                # Probability multiplier
                prob_multiplier = self.probability_multiplier_var.get()
                if prob_multiplier != 1.0:  # Only include if different from default
                    modification["probability_multiplier"] = prob_multiplier

                # NEW: Interferon multiplier
                interferon_multiplier = self.interferon_multiplier_var.get()
                if interferon_multiplier != 1.0:  # Only include if different from default
                    modification["interferon_multiplier"] = interferon_multiplier

                # Require at least one modification
                if not modification:
                    messagebox.showerror("Error", "At least one multiplier must be different from 1.0")
                    return

                self.result = {
                    "type": "modify_transition",
                    "rule_name": rule_name,
                    "modification": modification
                }

            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def cancel_clicked(self):
        """Handle Cancel button click"""
        self.result = None
        self.dialog.destroy()


class GameState:
    """
    Central run-level state (EP, deck, cycles) - UPDATED WITH MILESTONE TRACKING.
    - EP is a single decreasing counter.
    - Inserting and removing genes both SPEND EP (no refunds).
    - Costs come from the DB per-gene "cost" field (default 0).
    - Tracks build→play cycles and whether a gene offer is pending after Play.
    - Tracks selected starter entity for virus building.
    - NEW: Tracks milestone progress and achievements per run.
    """

    def __init__(self, *, offer_size: int = 5, seed: int | None = None):
        # Economy
        self.ep: int = 0

        # Deck-building
        self.deck: list[str] = []
        self.installed_genes: list[str] = []
        self.installs_this_round: int = 0

        # Starter entity selection and count
        self.selected_starter_entity: str = "unenveloped virion (extracellular)"  # Default fallback
        self.starting_entity_count: int = 10  # NEW: Dynamic starting count, increases when skipping gene offers

        # Gene-offer settings
        self.offer_size: int = offer_size

        # Build→Play cycle control
        self.cycle_limit: int = 10  # total allowed Play runs in a game
        self.cycles_used: int = 0  # how many Play runs have started
        self.offer_pending: bool = False  # set True by Play when exiting; handled by Controller

        # DB access
        self.db_manager = None  # set via set_database_manager()

        # RNG
        import random
        self._rng = random.Random(seed)

        # =================== MILESTONE TRACKING ===================

        # Milestone achievements for entire playthrough (persistent across play runs)
        self.achieved_milestones: set[str] = set()  # milestone IDs achieved in this playthrough

        # Milestone achievements for current play run only
        self.milestones_achieved_this_run: set[str] = set()  # reset each play run

        # Progress tracking for current play run (reset each play run)
        self.current_turn: int = 0
        self.peak_entity_counts: dict[str, int] = {}  # entity_class -> max count seen
        self.cumulative_entity_counts: dict[str, int] = {}  # entity_class -> total created

        # Milestone definitions (loaded from database)
        self._milestone_definitions: dict[str, dict] = {}

    # ------------ Wiring helpers ------------
    def set_database_manager(self, db_manager):
        self.db_manager = db_manager
        # Auto-select first available starter entity
        self._auto_select_starter_entity()
        # Load milestone definitions
        self._load_milestone_definitions()

    def _auto_select_starter_entity(self):
        """Automatically select the first available starter entity"""
        if not self.db_manager:
            return

        available_starters = self.db_manager.get_starter_entities()
        if available_starters:
            self.selected_starter_entity = available_starters[0]
        else:
            # Fallback to first entity if no starters defined
            all_entities = self.db_manager.get_all_entity_names()
            if all_entities:
                self.selected_starter_entity = all_entities[0]

    def _load_milestone_definitions(self):
        """Load milestone definitions from database"""
        if not self.db_manager:
            self._milestone_definitions = {}
            return

        self._milestone_definitions = self.db_manager.get_milestones()

    # ------------ Starter entity helpers ------------
    def get_available_starter_entities(self) -> list[str]:
        """Get all entities that can be used as starters"""
        if not self.db_manager:
            return []
        return self.db_manager.get_starter_entities()

    def set_starter_entity(self, entity_name: str) -> bool:
        """Set the selected starter entity (with validation)"""
        if not self.db_manager:
            return False

        available_starters = self.get_available_starter_entities()
        if entity_name in available_starters:
            self.selected_starter_entity = entity_name
            return True
        return False

    def get_selected_starter_entity(self) -> str:
        """Get the currently selected starter entity"""
        return self.selected_starter_entity

    def validate_starter_entity(self) -> tuple[bool, str]:
        """Validate current starter entity selection"""
        if not self.db_manager:
            return False, "No database loaded"

        available_starters = self.get_available_starter_entities()
        if not available_starters:
            return False, "No starter entities defined in database"

        if self.selected_starter_entity not in available_starters:
            # Try to auto-fix
            self._auto_select_starter_entity()
            if self.selected_starter_entity not in available_starters:
                return False, f"Selected starter entity '{self.selected_starter_entity}' is not available"

        return True, "Valid starter entity selected"

    # ------------ Cost helpers ------------
    def get_gene_cost(self, gene_name: str) -> int:
        if not self.db_manager:
            return 0
        gene = self.db_manager.get_gene(gene_name)
        return int(gene.get("cost", 0)) if gene else 0

    # ------------ EP Management (spending only, awards only for milestones) ------------

    def get_remove_cost(self, gene_name: str) -> int:
        """
        Flat EP cost to remove any gene.
        Kept as a method in case you want exceptions later.
        """
        return 10

    def can_afford_insert(self, gene_name: str) -> bool:
        return self.ep >= self.get_gene_cost(gene_name)

    def spend_for_insert(self, gene_name: str) -> bool:
        cost = self.get_gene_cost(gene_name)
        if self.ep >= cost:
            self.ep -= cost
            return True
        return False

    def can_afford_remove(self, gene_name: str) -> bool:
        return self.ep >= self.get_remove_cost(gene_name)

    def spend_for_remove(self, gene_name: str) -> bool:
        cost = self.get_remove_cost(gene_name)
        if self.ep >= cost:
            self.ep -= cost
            return True
        return False

    def award_ep(self, amount: int):
        """Award EP (used for milestone rewards only)"""
        if amount > 0:
            self.ep += amount

    # ------------ Deck helpers ------------
    def add_to_deck(self, gene_name: str) -> bool:
        if gene_name not in self.deck:
            self.deck.append(gene_name)
            return True
        return False

    def in_deck(self, gene_name: str) -> bool:
        return gene_name in self.deck

    # ------------ Offer helpers ------------
    def _all_gene_names(self) -> list[str]:
        if not self.db_manager:
            return []
        return list(self.db_manager.get_all_genes())

    def draw_gene_offers(self, n: int | None = None, exclude: set[str] | None = None) -> list[str]:
        n = n or self.offer_size
        exclude = exclude or set()
        pool = set(self._all_gene_names()) - set(self.deck) - set(exclude)
        pool_list = sorted(pool)
        if not pool_list:
            return []
        k = min(n, len(pool_list))
        return self._rng.sample(pool_list, k)

    # =================== MILESTONE SYSTEM ===================

    def reset_milestone_progress(self):
        """Reset milestone progress for a new play run (but keep playthrough achievements)"""
        # Reset current run progress but keep overall achievements
        self.milestones_achieved_this_run.clear()
        self.current_turn = 0
        self.peak_entity_counts.clear()
        self.cumulative_entity_counts.clear()

    def reset_for_new_game(self):
        """Reset all milestone data for a completely new game/playthrough"""
        self.achieved_milestones.clear()
        self.reset_milestone_progress()

    def update_turn_count(self, turn_number: int):
        """Update current turn number and check survival milestones"""
        self.current_turn = turn_number
        self._check_survival_milestones()

    def update_entity_counts(self, current_entities: dict[str, int], entities_created_this_turn: dict[str, int] = None):
        """
        Update entity count tracking and check entity count milestones

        Args:
            current_entities: Dict of entity_name -> current_count in simulation
            entities_created_this_turn: Dict of entity_name -> count created this turn (optional)
        """
        if not self.db_manager:
            return

        # Group current entities by class for peak tracking
        current_by_class = {}
        for entity_name, count in current_entities.items():
            entity_data = self.db_manager.get_entity(entity_name)
            if entity_data:
                entity_class = entity_data.get("entity_class", "unknown")
                current_by_class[entity_class] = current_by_class.get(entity_class, 0) + count

        # Update peak counts
        for entity_class, count in current_by_class.items():
            self.peak_entity_counts[entity_class] = max(
                self.peak_entity_counts.get(entity_class, 0),
                count
            )

        # Update cumulative counts if entities were created
        if entities_created_this_turn:
            for entity_name, count in entities_created_this_turn.items():
                entity_data = self.db_manager.get_entity(entity_name)
                if entity_data:
                    entity_class = entity_data.get("entity_class", "unknown")
                    self.cumulative_entity_counts[entity_class] = (
                            self.cumulative_entity_counts.get(entity_class, 0) + count
                    )

        # Check for newly achieved milestones
        self._check_entity_count_milestones()

    def _check_survival_milestones(self):
        """Check if any survival milestones have been achieved in this run"""
        for milestone_id, milestone in self._milestone_definitions.items():
            if (milestone["type"] == "survive_turns"
                    and milestone_id not in self.achieved_milestones  # Not already achieved in playthrough
                    and milestone_id not in self.milestones_achieved_this_run):  # Not already achieved this run
                if self.current_turn >= milestone["target"]:
                    self.milestones_achieved_this_run.add(milestone_id)
                    self.achieved_milestones.add(milestone_id)

    def _check_entity_count_milestones(self):
        """Check if any entity count milestones have been achieved in this run"""
        for milestone_id, milestone in self._milestone_definitions.items():
            if (milestone_id in self.achieved_milestones  # Already achieved in playthrough
                    or milestone_id in self.milestones_achieved_this_run):  # Already achieved this run
                continue

            milestone_type = milestone["type"]
            target = milestone["target"]
            entity_class = milestone.get("entity_class")

            if milestone_type == "peak_entity_count" and entity_class:
                current_peak = self.peak_entity_counts.get(entity_class, 0)
                if current_peak >= target:
                    self.milestones_achieved_this_run.add(milestone_id)
                    self.achieved_milestones.add(milestone_id)

            elif milestone_type == "cumulative_entity_count" and entity_class:
                current_cumulative = self.cumulative_entity_counts.get(entity_class, 0)
                if current_cumulative >= target:
                    self.milestones_achieved_this_run.add(milestone_id)
                    self.achieved_milestones.add(milestone_id)

    def get_milestone_progress(self) -> dict[str, dict]:
        """
        Get comprehensive milestone progress data for UI display

        Returns:
            Dict with structure:
            {
                "achieved": [list of achieved milestone data],
                "open": [list of open milestone data with progress],
                "total_ep_earned": int,
                "newly_achieved_this_run": [list of milestones achieved in current run]
            }
        """
        achieved = []
        open_milestones = []
        newly_achieved_this_run = []
        total_ep_earned = 0

        for milestone_id, milestone in self._milestone_definitions.items():
            milestone_data = milestone.copy()
            milestone_data["achieved"] = milestone_id in self.achieved_milestones
            milestone_data["achieved_this_run"] = milestone_id in self.milestones_achieved_this_run

            if milestone_data["achieved"]:
                achieved.append(milestone_data)
                total_ep_earned += milestone["reward_ep"]

                if milestone_data["achieved_this_run"]:
                    newly_achieved_this_run.append(milestone_data)
            else:
                # Add progress information for open milestones
                progress_info = self._get_milestone_progress_info(milestone)
                milestone_data.update(progress_info)
                open_milestones.append(milestone_data)

        return {
            "achieved": achieved,
            "open": open_milestones,
            "total_ep_earned": total_ep_earned,
            "newly_achieved_this_run": newly_achieved_this_run
        }

    def _get_milestone_progress_info(self, milestone: dict) -> dict:
        """Get progress information for a specific milestone"""
        milestone_type = milestone["type"]
        target = milestone["target"]

        if milestone_type == "survive_turns":
            current = self.current_turn
            return {
                "current_progress": current,
                "target_progress": target,
                "progress_description": f"{current}/{target} turns"
            }

        elif milestone_type == "peak_entity_count":
            entity_class = milestone.get("entity_class", "unknown")
            current = self.peak_entity_counts.get(entity_class, 0)
            return {
                "current_progress": current,
                "target_progress": target,
                "progress_description": f"{current}/{target} {entity_class} entities (peak)"
            }

        elif milestone_type == "cumulative_entity_count":
            entity_class = milestone.get("entity_class", "unknown")
            current = self.cumulative_entity_counts.get(entity_class, 0)
            return {
                "current_progress": current,
                "target_progress": target,
                "progress_description": f"{current}/{target} {entity_class} entities (total)"
            }

        else:
            return {
                "current_progress": 0,
                "target_progress": target,
                "progress_description": "Unknown milestone type"
            }

    def award_milestone_achievements(self) -> list[dict]:
        """
        Award EP for milestones achieved in THIS run only and return list of newly achieved milestones
        This should be called when returning from Play to Builder

        Returns:
            List of milestone data for milestones achieved in this specific run
        """
        newly_achieved = []

        # Only process milestones achieved in this run
        for milestone_id in self.milestones_achieved_this_run:
            milestone = self._milestone_definitions.get(milestone_id)
            if milestone:
                # Award EP
                reward_ep = milestone["reward_ep"]
                self.award_ep(reward_ep)

                # Collect for return
                milestone_copy = milestone.copy()
                milestone_copy["achieved"] = True
                newly_achieved.append(milestone_copy)

        return newly_achieved

    def get_available_milestones(self) -> list[dict]:
        """Get all milestone definitions from database"""
        return list(self._milestone_definitions.values())

    def refresh_milestone_definitions(self):
        """Refresh milestone definitions from database (call after database changes)"""
        self._load_milestone_definitions()

    def has_milestones_achieved_this_run(self) -> bool:
        """Check if any milestones were achieved in the current run"""
        return len(self.milestones_achieved_this_run) > 0

    def get_milestones_achieved_this_run(self) -> list[dict]:
        """Get list of milestones achieved in this specific run"""
        achieved_this_run = []
        for milestone_id in self.milestones_achieved_this_run:
            milestone = self._milestone_definitions.get(milestone_id)
            if milestone:
                milestone_copy = milestone.copy()
                milestone_copy["achieved"] = True
                milestone_copy["achieved_this_run"] = True
                achieved_this_run.append(milestone_copy)
        return achieved_this_run

    def increase_starting_entity_count(self, amount: int = 2):
        """Increase starting entity count (called when skipping gene offers)"""
        self.starting_entity_count += amount

    def get_starting_entity_count(self) -> int:
        """Get current starting entity count"""
        return self.starting_entity_count

    def reset_starting_entity_count(self):
        """Reset starting entity count to default (for new games)"""
        self.starting_entity_count = 10

    def can_install_gene_this_round(self) -> bool:
        return self.installs_this_round < 1

    def record_gene_install(self):
        self.installs_this_round += 1

    def reset_round_install_counter(self):
        self.installs_this_round = 0


class VirusSandboxController:
    """Main application controller - WITH MILESTONE SUPPORT AND SKIP ROUND FUNCTIONALITY"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Virus Sandbox")
        self.root.geometry("1200x800")
        self.root.minsize(900, 700)

        # Initialize modules
        self.modules = {}
        self.current_module = None
        self.current_database_manager = None

        # Persistent game state
        self.game_state = None

        self.setup_modules()
        self.switch_to_module("menu")

    def setup_modules(self):
        """Initialize all game modules"""
        self.modules["menu"] = MenuModule(self.root, self)
        self.modules["builder"] = BuilderModule(self.root, self)
        self.modules["play"] = PlayModule(self.root, self)
        self.modules["editor"] = EditorModule(self.root, self)

    def switch_to_module(self, module_name):
        """Switch to a different module and handle post-Play gene offer timing"""
        prev = self.current_module
        if self.current_module:
            self.modules[self.current_module].hide()

        if module_name not in self.modules:
            raise ValueError(f"Unknown module: {module_name}")

        self.current_module = module_name
        self.modules[module_name].show()

        # When returning FROM Play TO Builder, show the pending gene offer (if any)
        # NOTE: Milestone notifications and EP awards are handled by PlayModule.exit_to_builder() before this
        if prev == "play" and module_name == "builder" and self.game_state:
            self.game_state.reset_round_install_counter()
            if self.game_state.offer_pending:
                try:
                    self._show_gene_offer_dialog()
                finally:
                    self.game_state.offer_pending = False

        if prev == "play" and module_name == "builder" and self.game_state and self.game_state.offer_pending:
            try:
                self._show_gene_offer_dialog()
            finally:
                self.game_state.offer_pending = False  # ensure it's cleared even if dialog closed

    def start_new_game_with_database(self, database_manager):
        """Start new game with a loaded database - WITH MILESTONE INITIALIZATION"""
        self.current_database_manager = database_manager

        # Game state
        self.game_state = GameState(offer_size=5)
        self.game_state.set_database_manager(database_manager)
        self.game_state.cycle_limit = 10
        self.game_state.cycles_used = 0
        self.game_state.offer_pending = False

        # Reset all milestone data for new game
        self.game_state.reset_for_new_game()

        # NEW: Reset starting entity count for new game
        self.game_state.reset_starting_entity_count()

        # Seed deck with 10 random genes
        import random
        all_genes = database_manager.get_all_genes()
        initial_deck_size = min(60, len(all_genes))
        self.game_state.deck = random.sample(all_genes, initial_deck_size)
        self.game_state.ep = 100  # starting EP

        # Wire modules
        self.modules["builder"].set_database_manager(database_manager)
        self.modules["builder"].set_game_state(self.game_state)

        self.modules["play"].set_database_manager(database_manager)
        self.modules["play"].set_game_state(self.game_state)

        # Wire editor with database manager for milestone editing
        self.modules["editor"].db_manager = database_manager
        self.modules["editor"].update_database_display()
        self.modules["editor"].update_entity_list()
        self.modules["editor"].update_gene_list()
        self.modules["editor"].update_milestone_list()

        self.switch_to_module("builder")

    def start_simulation(self, virus_blueprint):
        """Start simulation with given virus blueprint (enforce cycle limit)"""
        if self.game_state and self.game_state.cycles_used >= self.game_state.cycle_limit:
            messagebox.showinfo("No Rounds Left", "You've used all available build→play rounds.")
            return

        # Count this Play run
        if self.game_state:
            self.game_state.cycles_used += 1
            self.game_state.offer_pending = False  # will be set True by Play on exit

        # NOTE: PlayModule.initialize_simulation() will call game_state.reset_milestone_progress()
        # to reset milestone progress for this specific play run
        self.modules["play"].set_virus_blueprint(virus_blueprint)
        self.modules["play"].set_game_state(self.game_state)
        self.switch_to_module("play")

    # =================== NEW: SKIP ROUND FUNCTIONALITY ===================

    def skip_round(self):
        """Skip the current round without playing - consumes a round but shows gene offer"""
        if not self.game_state:
            messagebox.showwarning("No Game State", "Game state not initialized.")
            return

        # Double-check round availability
        if self.game_state.cycles_used >= self.game_state.cycle_limit:
            messagebox.showwarning("No Rounds Left",
                                 f"You have used all {self.game_state.cycle_limit} available rounds.\n"
                                 "This game session is complete.")
            return

        # Count this as a used round
        self.game_state.cycles_used += 1
        self.game_state.reset_round_install_counter()

        # Show gene offer dialog directly (bypassing PlayModule and milestones)
        try:
            self._show_gene_offer_dialog()
        except Exception as e:
            # If gene offer fails, at least update the UI
            messagebox.showerror("Gene Offer Error", f"Error showing gene offer: {e}")

        # Update builder UI to reflect the consumed round
        builder = self.modules.get("builder")
        if builder:
            try:
                builder.update_virus_display()  # This will update the rounds counter
            except Exception:
                pass

    # =================== EXISTING METHODS (UNCHANGED) ===================

    def _show_gene_offer_dialog(self):
        """Offer exactly one of up to 5 random genes to add to the deck (after Play ends) - WITH STARTING COUNT BONUS."""
        if not (self.current_database_manager and self.game_state):
            return

        # Build exclusion: already in deck or currently installed
        exclude = set(self.game_state.deck) | set(self.game_state.installed_genes)

        import random
        all_genes = list(self.current_database_manager.get_all_genes())
        pool = [g for g in all_genes if g not in exclude]
        if not pool:
            messagebox.showinfo("Gene Offer", "No new genes are available.")
            return

        k = min(self.game_state.offer_size, len(pool))
        offers = random.sample(pool, k)

        # Modal dialog - IMPROVED CENTERING
        dialog = tk.Toplevel(self.root)
        dialog.title("Evolutionary Opportunity")
        dialog.geometry("460x360")  # Slightly larger to accommodate bonus info
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog properly
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (230)  # Half of dialog width (460/2)
        y = (dialog.winfo_screenheight() // 2) - (180)  # Half of dialog height (360/2)
        dialog.geometry(f"460x360+{x}+{y}")

        # Header with better styling
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(header_frame, text="Evolutionary Opportunity", font=("Arial", 14, "bold")).pack()
        ttk.Label(header_frame, text="Select ONE new gene to add to your deck:",
                  font=("Arial", 11)).pack(pady=(10, 0))

        # Gene selection area
        selection_frame = ttk.Frame(dialog)
        selection_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        listbox = tk.Listbox(selection_frame, height=min(10, len(offers)), font=("Arial", 10))
        for name in offers:
            cost = 0
            gene = self.current_database_manager.get_gene(name)
            if gene:
                cost = gene.get("cost", 0)
            listbox.insert(tk.END, f"{name} ({cost} EP)")
        listbox.pack(fill=tk.BOTH, expand=True)

        # NEW: Starting count bonus info
        bonus_frame = ttk.Frame(dialog)
        bonus_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        current_count = self.game_state.get_starting_entity_count()
        if current_count > 10:
            bonus_text = f"Current starting entities: {current_count} (bonus: +{current_count - 10})"
            ttk.Label(bonus_frame, text=bonus_text, font=("Arial", 10, "italic"),
                      foreground="blue").pack()

        selection_holder = {"choice": None}

        def choose_and_close():
            sel = listbox.curselection()
            if sel:
                display = listbox.get(sel[0])
                gene_name = display.split(" (")[0]
                selection_holder["choice"] = gene_name
            dialog.destroy()

        def skip_and_get_bonus():
            """Skip gene selection and get starting entity bonus"""
            self.game_state.increase_starting_entity_count(2)
            dialog.destroy()

        # Button area
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Button(button_frame, text="Add Selected Gene", command=choose_and_close).pack(side=tk.LEFT, padx=(0, 10))

        # NEW: Skip button with bonus indication
        skip_text = f"Skip (+2 starting entities)"
        ttk.Button(button_frame, text=skip_text, command=skip_and_get_bonus).pack(side=tk.LEFT)

        # Focus and keyboard handling
        dialog.focus_set()
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.bind('<Return>', lambda e: choose_and_close())

        # CRITICAL: Wait for dialog to close (this was already there, but keeping it clear)
        self.root.wait_window(dialog)

        picked = selection_holder["choice"]
        if picked:
            if self.game_state.add_to_deck(picked):
                messagebox.showinfo("Gene Added", f"Added to deck: {picked}")
            else:
                messagebox.showinfo("No Change", f"{picked} was already in your deck.")
        else:
            # NEW: Show bonus confirmation if they skipped
            new_count = self.game_state.get_starting_entity_count()
            if new_count > current_count:
                messagebox.showinfo("Starting Bonus",
                                    f"You now start with {new_count} entities instead of 10!\n"
                                    f"(Bonus: +{new_count - 10} entities)")

        # Refresh Builder UI so changes appear immediately
        builder = self.modules.get("builder")
        if builder:
            try:
                builder.update_gene_list()
                builder.update_virus_display()
            except Exception:
                pass

    def quit_application(self):
        """Exit the application"""
        # Check for unsaved changes in editor (including milestones)
        if (hasattr(self.modules["editor"], 'db_manager') and
                self.modules["editor"].db_manager.is_modified):
            result = messagebox.askyesnocancel("Unsaved Changes",
                                               "You have unsaved changes in the gene editor. Save before exiting?")
            if result is True:
                try:
                    self.modules["editor"].save_database()
                except:
                    pass
            elif result is None:
                return

        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.root.quit()

    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        self.root.mainloop()

    # =================== MILESTONE-RELATED HELPER METHODS ===================

    def handle_database_change(self):
        """Handle database changes that might affect milestones"""
        # Refresh milestone definitions in game state
        if self.game_state:
            self.game_state.refresh_milestone_definitions()

        # Update any modules that display milestone information
        if self.current_module == "builder":
            try:
                # Builder might want to refresh milestone-related displays in the future
                pass
            except Exception:
                pass

    def validate_current_milestones(self):
        """Validate that current milestone definitions are still valid"""
        if not (self.game_state and self.current_database_manager):
            return True, "No milestones to validate"

        try:
            milestones = self.current_database_manager.get_milestones()
            invalid_milestones = []

            for milestone_id, milestone_data in milestones.items():
                is_valid, error_msg = self.current_database_manager.validate_milestone_data(milestone_data)
                if not is_valid:
                    invalid_milestones.append(f"{milestone_id}: {error_msg}")

            if invalid_milestones:
                return False, f"Invalid milestones found:\n" + "\n".join(invalid_milestones)

            return True, "All milestones are valid"

        except Exception as e:
            return False, f"Error validating milestones: {e}"

    def show_milestone_validation_errors(self):
        """Show milestone validation errors to user"""
        is_valid, message = self.validate_current_milestones()
        if not is_valid:
            messagebox.showerror("Milestone Validation Error", message)
            return False
        return True


if __name__ == "__main__":
    app = VirusSandboxController()
    app.run()