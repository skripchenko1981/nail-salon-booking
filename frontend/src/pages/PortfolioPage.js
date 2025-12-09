import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function PortfolioPage() {
  const navigate = useNavigate();
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    fetchImages();
  }, []);

  const fetchImages = async () => {
    try {
      const response = await axios.get(`${API}/gallery`);
      setImages(response.data);
    } catch (error) {
      console.error('Помилка завантаження галереї:', error);
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#FDFCFB] to-[#F3EBEB] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#D4A5A5] mx-auto"></div>
          <p className="mt-4 text-gray-600">Завантаження...</p>
        </div>
      </div>
    );
  }

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
      <div className="pt-24 pb-12 px-6">
        <div className="container mx-auto max-w-7xl text-center">
          <h2 className="text-5xl md:text-6xl font-bold mb-4" style={{ fontFamily: 'Playfair Display, serif' }}>
            Наші роботи
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Портфоліо наших майстрів - ідеї та натхнення для вашого наступного манікюру
          </p>
        </div>
      </div>

      {/* Gallery Grid */}
      <div className="container mx-auto max-w-7xl px-6 pb-20">
        {images.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-600 text-lg">Галерея ще порожня</p>
            <p className="text-gray-400 mt-2">Скоро тут з'являться наші роботи</p>
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
