import React, { useState, useEffect } from 'react';
import { Loader2, AlertTriangle } from 'lucide-react';
import { getAvailableSkills, loadSkillSettings } from '../utils/skillRegistry';

const SkillPage = ({ skillId }) => {
    const [Component, setComponent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let mounted = true;

        const load = async () => {
            setLoading(true);
            setError(null);
            try {
                const skills = getAvailableSkills();
                // Check if skill exists in registry (based on file existence)
                const skillExists = skills.some(s => s.id === skillId);

                if (!skillExists) {
                    throw new Error(`Skill '${skillId}' settings not found.`);
                }

                const LoadedComponent = await loadSkillSettings(skillId);
                if (mounted) {
                    if (LoadedComponent) {
                        setComponent(() => LoadedComponent);
                    } else {
                        throw new Error("Failed to load component");
                    }
                }
            } catch (err) {
                if (mounted) setError(err.message);
            } finally {
                if (mounted) setLoading(false);
            }
        };

        if (skillId) {
            load();
        }

        return () => { mounted = false; };
    }, [skillId]);

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center text-mainframe-text/50">
                <Loader2 className="animate-spin mr-2" /> Loading '{skillId}'...
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-full items-center justify-center text-red-400">
                <AlertTriangle className="mr-2" /> {error}
            </div>
        );
    }

    if (!Component) {
        return (
            <div className="flex h-full items-center justify-center text-mainframe-text/50">
                Component not found.
            </div>
        );
    }

    // Render the dynamically loaded component
    // We can pass common props here if needed, like global settings or a save handler
    return <Component />;
};

export default SkillPage;
