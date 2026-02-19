import { Bot, Activity, Terminal, Code, Cpu, HardDrive, Wifi, Cloud, Zap, Home } from 'lucide-react';

// Map skill names to Lucide icons
const SKILL_ICONS = {
    'codex': Terminal,
    'garmin': Activity,
    'strava': Activity,
    'homeassistant': Home,
    'weather': Cloud,
    'tibber': Zap,
    'withings': Activity,
    'roborock': Bot,
    'google_calendar': Bot,
    'pfsense': Wifi,
    'default': Cpu
};

export const getSkillIcon = (skillName) => {
    return SKILL_ICONS[skillName.toLowerCase()] || SKILL_ICONS.default;
};

// Use Vite's glob import to find all Settings.jsx files in skills directory
// Using relative path to avoid alias issues without server restart
const skillSettingsModules = import.meta.glob('../../../skills/*/Settings.jsx');

export const getAvailableSkills = () => {
    const skills = [];

    console.log("Skill Registry: Glob results:", Object.keys(skillSettingsModules));

    for (const path in skillSettingsModules) {
        // Path example: "../../../skills/garmin/Settings.jsx"
        const match = path.match(/\/skills\/([^/]+)\/Settings\.jsx$/);
        if (match) {
            const skillName = match[1];
            skills.push({
                id: skillName,
                name: skillName.charAt(0).toUpperCase() + skillName.slice(1).replace(/_/g, ' '),
                path: path,
                loader: skillSettingsModules[path]
            });
        }
    }

    return skills.sort((a, b) => a.name.localeCompare(b.name));
};

export const loadSkillSettings = async (skillId) => {
    const skills = getAvailableSkills();
    const skill = skills.find(s => s.id === skillId);
    if (!skill) return null;

    try {
        const module = await skill.loader();
        return module.default;
    } catch (e) {
        console.error(`Skill Registry: Failed to load module for ${skillId}`, e);
        return null;
    }
};
