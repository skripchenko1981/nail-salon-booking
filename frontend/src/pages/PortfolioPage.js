import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, ChevronLeft, ChevronRight, User } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function PortfolioPage() {
  const navigate = useNavigate();
  const [masters, setMasters] = useState([]);
  const [selectedMaster, setSelectedMaster] = useState(null);
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    fetchMasters();
  }, []);

  useEffect(() => {
    if (selectedMaster) {
      fetchMasterGallery(selectedMaster.id);
    }
  }, [selectedMaster]);

  const fetchMasters = async () => {
    try {
      const response = await axios.get(`${API}/masters`);
      const activeMasters = response.data.filter(m => m.is_active);
      setMasters(activeMasters);
      
      // Вибрати першого майстра за замовчуванням
      if (activeMasters.length > 0) {
        setSelectedMaster(activeMasters[0]);
      } else {
        setLoading(false);
      }
    } catch (error) {
      console.error('Помилка завантаження майстрів:', error);
      setLoading(false);
    }
  };

  const fetchMasterGallery = async (masterId) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/masters/${masterId}/gallery`);
      setImages(response.data);
    } catch (error) {
      console.error('Помилка завантаження галереї:', error);
      setImages([]);
    } finally {
      setLoading(false);
    }
  };

  const openLightbox = (index) => {
    setCurrentIndex(index);
    setLightboxOpen(true);
  };

  const closeLightbox = () => {
    setLightboxOpen(false);
  };

  const nextImage = () => {
    setCurrentIndex((prev) => (prev + 1) % images.length);
  };

  const prevImage = () => {
    setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FDFCFB] to-[#F3EBEB]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-rose-200/50">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <h1 
            className="text-2xl font-bold tracking-tight cursor-pointer" 
            style={{ fontFamily: 'Playfair Display, serif' }}
            onClick={() => navigate('/')}
          >
            Nail Studio
          </h1>
          <button 
            onClick={() => navigate('/')} 
            className="text-sm hover:text-[#D4A5A5] transition-colors"
          >
            ← Повернутися на головну
          </button>
        </div>
      </nav>

      {/* Hero */}
      <div className="pt-24 pb-8 px-6">
        <div className="container mx-auto max-w-7xl text-center">
          <h2 className="text-5xl md:text-6xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
            Портфоліо
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Оберіть майстра щоб переглянути його роботи
          </p>
        </div>
      </div>

      {/* Masters Tabs */}
      <div className="container mx-auto max-w-7xl px-6 pb-8">
        <div className="flex flex-wrap justify-center gap-3">
          {masters.map((master) => (
            <button
              key={master.id}
              onClick={() => setSelectedMaster(master)}
              className={`flex items-center gap-2 px-6 py-3 rounded-full font-medium transition-all ${
                selectedMaster?.id === master.id
                  ? 'bg-[#D4A5A5] text-white shadow-lg'
                  : 'bg-white border-2 border-rose-200/50 text-gray-700 hover:border-[#D4A5A5]'
              }`}
              data-testid={`master-tab-${master.id}`}
            >
              {master.photo_url ? (
                <img 
                  src={master.photo_url} 
                  alt={master.name}
                  className="w-8 h-8 rounded-full object-cover"
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-rose-100 flex items-center justify-center">
                  <User className="w-4 h-4 text-[#D4A5A5]" />
                </div>
              )}
              <span>{master.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Selected Master Info */}
      {selectedMaster && (
        <div className="container mx-auto max-w-7xl px-6 pb-8">
          <div className="bg-white rounded-2xl p-6 border border-rose-200/50 shadow-sm">
            <div className="flex items-center gap-4">
              {selectedMaster.photo_url ? (
                <img 
                  src={selectedMaster.photo_url} 
                  alt={selectedMaster.name}
                  className="w-16 h-16 rounded-full object-cover"
                />
              ) : (
                <div className="w-16 h-16 rounded-full bg-rose-100 flex items-center justify-center">
                  <User className="w-8 h-8 text-[#D4A5A5]" />
                </div>
              )}
              <div>
                <h3 className="text-2xl font-bold" style={{ fontFamily: 'Playfair Display, serif' }}>
                  {selectedMaster.name}
                </h3>
                {selectedMaster.bio && (
                  <p className="text-gray-600 mt-1">{selectedMaster.bio}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Gallery Grid */}
      <div className="container mx-auto max-w-7xl px-6 pb-20">
        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#D4A5A5] mx-auto"></div>
            <p className="mt-4 text-gray-600">Завантаження...</p>
          </div>
        ) : images.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-600 text-lg">
              {selectedMaster ? `У майстра ${selectedMaster.name} ще немає фото в портфоліо` : 'Оберіть майстра'}
            </p>
            <p className="text-gray-400 mt-2">Скоро тут з'являться роботи</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {images.map((image, index) => (
              <div
                key={image.id}
                className="relative aspect-square rounded-xl overflow-hidden cursor-pointer group"
                onClick={() => openLightbox(index)}
              >
                <img
                  src={image.image_url}
                  alt={image.description || `Gallery image ${index + 1}`}
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                  onError={(e) => {
                    e.target.src = 'https://via.placeholder.com/400x400?text=Фото';
                  }}
                />
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all flex items-center justify-center">
                  <div className="text-white opacity-0 group-hover:opacity-100 transition-opacity">
                    <p className="text-sm font-medium">Переглянути</p>
                  </div>
                </div>
                {image.description && (
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <p className="text-white text-sm">{image.description}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Lightbox */}
      {lightboxOpen && images.length > 0 && (
        <div className="fixed inset-0 bg-black bg-opacity-95 z-50 flex items-center justify-center p-4">
          {/* Close button */}
          <button
            onClick={closeLightbox}
            className="absolute top-4 right-4 text-white hover:text-gray-300 transition-colors z-10"
          >
            <X className="h-8 w-8" />
          </button>

          {/* Previous button */}
          {images.length > 1 && (
            <button
              onClick={prevImage}
              className="absolute left-4 text-white hover:text-gray-300 transition-colors z-10"
            >
              <ChevronLeft className="h-12 w-12" />
            </button>
          )}

          {/* Image */}
          <div className="max-w-6xl max-h-[90vh] flex flex-col items-center">
            <img
              src={images[currentIndex].image_url}
              alt={images[currentIndex].description || 'Gallery image'}
              className="max-w-full max-h-[80vh] object-contain rounded-lg"
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/800x600?text=Фото';
              }}
            />
            {images[currentIndex].description && (
              <p className="text-white mt-4 text-center max-w-2xl">
                {images[currentIndex].description}
              </p>
            )}
            <p className="text-gray-400 mt-2 text-sm">
              {currentIndex + 1} / {images.length}
            </p>
          </div>

          {/* Next button */}
          {images.length > 1 && (
            <button
              onClick={nextImage}
              className="absolute right-4 text-white hover:text-gray-300 transition-colors z-10"
            >
              <ChevronRight className="h-12 w-12" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default PortfolioPage;
