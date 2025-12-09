// Визначення тем для Nail Studio
export const themes = {
  classic: {
    name: 'Класична',
    season: 'Цілорічно',
    colors: {
      primary: '#D4A5A5',
      secondary: '#9E829C',
      accent: '#F3EBEB',
      background: 'from-[#FDFCFB] to-[#F3EBEB]',
      text: '#1F2937',
      border: 'border-rose-200/50'
    },
    decorations: null
  },
  
  winter: {
    name: 'Новорічна',
    season: 'Грудень - Січень',
    colors: {
      primary: '#3B82F6',
      secondary: '#60A5FA',
      accent: '#EFF6FF',
      background: 'from-[#F0F9FF] to-[#DBEAFE]',
      text: '#1E3A8A',
      border: 'border-blue-200/50'
    },
    decorations: 'snowflakes' // Сніжинки
  },
  
  spring: {
    name: 'Весняна',
    season: 'Березень - Травень',
    colors: {
      primary: '#EC4899',
      secondary: '#F472B6',
      accent: '#FDF2F8',
      background: 'from-[#FDF2F8] to-[#FCE7F3]',
      text: '#831843',
      border: 'border-pink-200/50'
    },
    decorations: 'flowers' // Квіти
  },
  
  summer: {
    name: 'Літня',
    season: 'Червень - Серпень',
    colors: {
      primary: '#F59E0B',
      secondary: '#FBBF24',
      accent: '#FFFBEB',
      background: 'from-[#FFFBEB] to-[#FEF3C7]',
      text: '#78350F',
      border: 'border-amber-200/50'
    },
    decorations: 'sun' // Сонце та промені
  },
  
  autumn: {
    name: 'Осіння',
    season: 'Вересень - Листопад',
    colors: {
      primary: '#EA580C',
      secondary: '#FB923C',
      accent: '#FFF7ED',
      background: 'from-[#FFF7ED] to-[#FFEDD5]',
      text: '#7C2D12',
      border: 'border-orange-200/50'
    },
    decorations: 'leaves' // Листя
  }
};

// Автоматичний вибір теми за місяцем
export const getSeasonalTheme = () => {
  const month = new Date().getMonth(); // 0-11
  
  if (month === 11 || month === 0) return 'winter';      // Грудень, Січень
  if (month >= 2 && month <= 4) return 'spring';         // Березень-Травень
  if (month >= 5 && month <= 7) return 'summer';         // Червень-Серпень
  if (month >= 8 && month <= 10) return 'autumn';        // Вересень-Листопад
  
  return 'classic';
};
