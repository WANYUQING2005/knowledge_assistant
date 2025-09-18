import { useState, useCallback } from "react";
export const useKnowledgeSelector = (initialSelectedKBs = []) => {
  const [selectedKBs, setSelectedKBs] = useState(initialSelectedKBs);
  const [isKBPickerOpen, setIsKBPickerOpen] = useState(false);
  const openKBPicker = useCallback(() => {
    setIsKBPickerOpen(true);
  }, []);
  const closeKBPicker = useCallback(() => {
    setIsKBPickerOpen(false);
  }, []);
  const handleKBChange = useCallback((newSelectedKBs) => {
    setSelectedKBs(newSelectedKBs);
  }, []);
  const clearSelectedKBs = useCallback(() => {
    setSelectedKBs([]);
  }, []);
  const toggleKB = useCallback((kb) => {
    setSelectedKBs((prev) => {
      const isSelected = prev.some((selected) => selected.id === kb.id);
      if (isSelected) {
        return prev.filter((selected) => selected.id !== kb.id);
      } else {
        return [...prev, kb];
      }
    });
  }, []);
  const getSelectedKBIds = useCallback(() => {
    return selectedKBs.map((kb) => kb.id);
  }, [selectedKBs]);
  const getSelectedKBNames = useCallback(() => {
    return selectedKBs.map((kb) => kb.name);
  }, [selectedKBs]);
  return {
    selectedKBs,
    isKBPickerOpen,
    openKBPicker,
    closeKBPicker,
    handleKBChange,
    clearSelectedKBs,
    toggleKB,
    getSelectedKBIds,
    getSelectedKBNames,
  };
};
