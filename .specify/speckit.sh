#!/usr/bin/env bash
# SpecKit Shell Helpers
# Source tento soubor pro snadné použití SpecKit příkazů
#
# Usage:
#   source .specify/speckit.sh
#   nebo přidejte do ~/.bashrc nebo ~/.zshrc:
#   source /path/to/Langchain-benjamin/.specify/speckit.sh

# Get the directory where this script is located
SPECKIT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SPECKIT_DIR/.." && pwd)"

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# SpecKit banner
speckit_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║        SpecKit Development Tool        ║"
    echo "║    Czech MedAI (Benjamin) Project      ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Create new feature
speckit_new() {
    if [ -z "$1" ]; then
        echo -e "${RED}Error: Feature description required${NC}"
        echo "Usage: speckit_new 'Feature description' [--short-name name] [--number N]"
        echo ""
        echo "Examples:"
        echo "  speckit_new 'Add PubMed agent'"
        echo "  speckit_new 'OAuth integration' --short-name oauth"
        echo "  speckit_new 'User auth' --number 10"
        return 1
    fi

    echo -e "${BLUE}Creating new feature...${NC}"
    "$SPECKIT_DIR/scripts/bash/create-new-feature.sh" "$@"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Feature created successfully!${NC}"
        echo -e "${YELLOW}Next steps:${NC}"
        echo "  1. Edit spec: vim specs/*/spec.md"
        echo "  2. Or use Claude Code: /speckit.specify"
    else
        echo -e "${RED}✗ Failed to create feature${NC}"
        return 1
    fi
}

# Setup implementation plan
speckit_plan() {
    echo -e "${BLUE}Setting up implementation plan...${NC}"
    "$SPECKIT_DIR/scripts/bash/setup-plan.sh"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Plan setup complete!${NC}"
        echo -e "${YELLOW}Next steps:${NC}"
        echo "  1. Edit plan: vim specs/*/plan.md"
        echo "  2. Or use Claude Code: /speckit.plan"
    else
        echo -e "${RED}✗ Failed to setup plan${NC}"
        return 1
    fi
}

# Check prerequisites
speckit_check() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    "$SPECKIT_DIR/scripts/bash/check-prerequisites.sh"
}

# Update agent context
speckit_update() {
    echo -e "${BLUE}Updating agent context...${NC}"
    "$SPECKIT_DIR/scripts/bash/update-agent-context.sh"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Agent context updated!${NC}"
    else
        echo -e "${RED}✗ Failed to update context${NC}"
        return 1
    fi
}

# Show current feature info
speckit_info() {
    source "$SPECKIT_DIR/scripts/bash/common.sh"
    eval $(get_feature_paths)

    echo -e "${BLUE}Current Feature Information${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Repository:     ${GREEN}$REPO_ROOT${NC}"
    echo -e "Current Branch: ${YELLOW}$CURRENT_BRANCH${NC}"
    echo -e "Feature Dir:    ${GREEN}$FEATURE_DIR${NC}"
    echo ""

    if [ -f "$FEATURE_SPEC" ]; then
        echo -e "Files:"
        echo -e "  ${GREEN}✓${NC} spec.md"
    else
        echo -e "  ${RED}✗${NC} spec.md (missing)"
    fi

    if [ -f "$IMPL_PLAN" ]; then
        echo -e "  ${GREEN}✓${NC} plan.md"
    else
        echo -e "  ${YELLOW}⚠${NC} plan.md (not created yet)"
    fi

    if [ -f "$TASKS" ]; then
        echo -e "  ${GREEN}✓${NC} tasks.md"
    else
        echo -e "  ${YELLOW}⚠${NC} tasks.md (not created yet)"
    fi
}

# Go to feature directory
speckit_cd() {
    source "$SPECKIT_DIR/scripts/bash/common.sh"
    eval $(get_feature_paths)

    if [ -d "$FEATURE_DIR" ]; then
        cd "$FEATURE_DIR" || return 1
        echo -e "${GREEN}Changed to feature directory: $FEATURE_DIR${NC}"
        ls -la
    else
        echo -e "${RED}Feature directory not found: $FEATURE_DIR${NC}"
        return 1
    fi
}

# Edit current feature spec
speckit_edit_spec() {
    source "$SPECKIT_DIR/scripts/bash/common.sh"
    eval $(get_feature_paths)

    if [ -f "$FEATURE_SPEC" ]; then
        ${EDITOR:-vim} "$FEATURE_SPEC"
    else
        echo -e "${RED}Spec file not found: $FEATURE_SPEC${NC}"
        return 1
    fi
}

# Edit current feature plan
speckit_edit_plan() {
    source "$SPECKIT_DIR/scripts/bash/common.sh"
    eval $(get_feature_paths)

    if [ -f "$IMPL_PLAN" ]; then
        ${EDITOR:-vim} "$IMPL_PLAN"
    else
        echo -e "${YELLOW}Plan file not found. Creating...${NC}"
        speckit_plan
        if [ -f "$IMPL_PLAN" ]; then
            ${EDITOR:-vim} "$IMPL_PLAN"
        fi
    fi
}

# Edit current feature tasks
speckit_edit_tasks() {
    source "$SPECKIT_DIR/scripts/bash/common.sh"
    eval $(get_feature_paths)

    if [ -f "$TASKS" ]; then
        ${EDITOR:-vim} "$TASKS"
    else
        echo -e "${RED}Tasks file not found: $TASKS${NC}"
        echo "Use Claude Code: /speckit.tasks"
        return 1
    fi
}

# List all features
speckit_list() {
    echo -e "${BLUE}All Features${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ -d "$REPO_ROOT/specs" ]; then
        for dir in "$REPO_ROOT/specs"/*; do
            if [ -d "$dir" ]; then
                dirname=$(basename "$dir")
                # Check if it's a feature directory (starts with number)
                if [[ "$dirname" =~ ^[0-9]{3}- ]]; then
                    # Check for spec.md
                    if [ -f "$dir/spec.md" ]; then
                        echo -e "  ${GREEN}✓${NC} $dirname"
                    else
                        echo -e "  ${YELLOW}⚠${NC} $dirname (no spec)"
                    fi
                fi
            fi
        done
    else
        echo -e "${YELLOW}No specs directory found${NC}"
    fi
}

# Show help
speckit_help() {
    speckit_banner
    echo "Available Commands:"
    echo ""
    echo -e "${GREEN}Feature Management:${NC}"
    echo "  speckit_new <description>     - Create new feature branch and spec"
    echo "  speckit_plan                  - Setup implementation plan"
    echo "  speckit_info                  - Show current feature information"
    echo "  speckit_list                  - List all features"
    echo ""
    echo -e "${GREEN}Navigation:${NC}"
    echo "  speckit_cd                    - Change to current feature directory"
    echo "  speckit_edit_spec             - Edit current spec.md"
    echo "  speckit_edit_plan             - Edit current plan.md"
    echo "  speckit_edit_tasks            - Edit current tasks.md"
    echo ""
    echo -e "${GREEN}Utilities:${NC}"
    echo "  speckit_check                 - Check prerequisites"
    echo "  speckit_update                - Update agent context"
    echo "  speckit_help                  - Show this help"
    echo ""
    echo -e "${YELLOW}Shortcuts (aliases):${NC}"
    echo "  sn <description>              - Alias for speckit_new"
    echo "  sp                            - Alias for speckit_plan"
    echo "  si                            - Alias for speckit_info"
    echo "  sc                            - Alias for speckit_check"
    echo "  sed                           - Alias for speckit_edit_spec"
    echo "  ped                           - Alias for speckit_edit_plan"
    echo ""
    echo -e "${BLUE}Claude Code Commands (use in Claude Code):${NC}"
    echo "  /speckit.constitution         - Manage project constitution"
    echo "  /speckit.specify              - Create feature specification"
    echo "  /speckit.analyze              - Analyze spec"
    echo "  /speckit.clarify              - Resolve ambiguities"
    echo "  /speckit.plan                 - Create implementation plan"
    echo "  /speckit.tasks                - Generate task breakdown"
    echo "  /speckit.implement            - AI-assisted implementation"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "  QUICKSTART.md                 - Quick start guide"
    echo "  CLAUDE.md                     - Claude Code guide"
    echo "  .specify/README.md            - SpecKit documentation"
    echo "  .specify/memory/constitution.md - Project Constitution"
    echo ""
}

# Shortcuts (aliases)
alias sn='speckit_new'
alias sp='speckit_plan'
alias si='speckit_info'
alias sc='speckit_check'
alias sl='speckit_list'
alias sed='speckit_edit_spec'
alias ped='speckit_edit_plan'
alias ted='speckit_edit_tasks'

# Tab completion for speckit_new (bash only)
if [ -n "$BASH_VERSION" ]; then
    _speckit_new_completion() {
        local cur="${COMP_WORDS[COMP_CWORD]}"
        local opts="--short-name --number --json --help"
        COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
    }
    complete -F _speckit_new_completion speckit_new
    complete -F _speckit_new_completion sn
fi

# Show banner on load
echo -e "${GREEN}✓ SpecKit helpers loaded!${NC}"
echo "Type ${YELLOW}speckit_help${NC} for available commands"
