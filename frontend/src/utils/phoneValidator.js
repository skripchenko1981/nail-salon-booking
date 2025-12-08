/**
 * Валідація та форматування українських телефонів
 */

export const validateUkrainianPhone = (phone) => {
  // Видаляємо всі символи крім цифр та +
  const cleaned = phone.replace(/[^\d+]/g, '');
  
  // Перевіряємо різні формати
  const patterns = [
    /^\+380\d{9}$/,  // +380XXXXXXXXX
    /^380\d{9}$/,     // 380XXXXXXXXX
    /^0\d{9}$/,       // 0XXXXXXXXX
  ];
  
  for (const pattern of patterns) {
    if (pattern.test(cleaned)) {
      return true;
    }
  }
  
  return false;
};

export const formatUkrainianPhone = (phone) => {
  const cleaned = phone.replace(/[^\d+]/g, '');
  
  // Конвертуємо до формату +380XXXXXXXXX
  if (cleaned.startsWith('+380')) {
    return cleaned;
  } else if (cleaned.startsWith('380')) {
    return '+' + cleaned;
  } else if (cleaned.startsWith('0')) {
    return '+38' + cleaned;
  }
  
  return phone;
};

export const formatPhoneForDisplay = (phone) => {
  // +380XXXXXXXXX -> +380 XX XXX XX XX
  const cleaned = phone.replace(/[^\d+]/g, '');
  
  if (cleaned.startsWith('+380') && cleaned.length === 13) {
    return `+380 ${cleaned.substring(4, 6)} ${cleaned.substring(6, 9)} ${cleaned.substring(9, 11)} ${cleaned.substring(11, 13)}`;
  }
  
  return phone;
};

export const getPhoneInputMask = () => {
  return '+380 ## ### ## ##';
};