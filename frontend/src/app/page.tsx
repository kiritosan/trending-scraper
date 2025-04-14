'use client';

import { useState, useEffect } from 'react';
import { Tab } from '@headlessui/react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUpIcon, ArrowTrendingUpIcon, GlobeAltIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

// API基础URL
const API_BASE_URL = 'http://localhost:8000';

// 平台类型
interface Platform {
  id: string;
  name: string;
}

// 趋势项类型
interface TrendingItem {
  title: string;
  url: string;
  rank: number;
  score: number | null;
  author: string | null;
  description: string | null;
  timestamp: string | null;
  platform: string;
  category: string | null;
  extra_data: Record<string, any>;
}

// 平台数据类型
interface PlatformData {
  platform: string;
  display_name: string;
  items: TrendingItem[];
}

export default function Home() {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [trendingData, setTrendingData] = useState<PlatformData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  // 获取平台列表
  useEffect(() => {
    const fetchPlatforms = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/platforms`);
        setPlatforms(response.data.platforms);
        if (response.data.platforms.length > 0) {
          setSelectedPlatform(response.data.platforms[0].id);
        }
      } catch (err) {
        console.error('Error fetching platforms:', err);
        setError('无法获取平台列表，请确保API服务器正在运行。');
      }
    };

    fetchPlatforms();
  }, []);

  // 获取趋势数据
  useEffect(() => {
    const fetchTrendingData = async () => {
      if (!selectedPlatform) return;
      
      setLoading(true);
      setError(null);
      
      try {
        console.log(`Fetching data for platform: ${selectedPlatform}`);
        
        // 如果选择了"all"，获取所有平台数据
        if (selectedPlatform === 'all') {
          const response = await axios.get(`${API_BASE_URL}/trending`);
          console.log('All platforms response:', response.data);
          setTrendingData(response.data.platforms || []);
        } else {
          // 获取特定平台数据
          const response = await axios.get(`${API_BASE_URL}/trending/${selectedPlatform}`);
          console.log(`${selectedPlatform} response:`, response.data);
          
          // API返回的单个平台数据包含platform、display_name和items字段
          if (response.data && Array.isArray(response.data.items)) {
            // 将单个平台数据包装成数组格式以保持一致性
            setTrendingData([{
              platform: response.data.platform,
              display_name: response.data.display_name,
              items: response.data.items
            }]);
          } else {
            console.error('Invalid response format:', response.data);
            setError(`获取${selectedPlatform}数据格式错误`);
          }
        }
      } catch (err) {
        console.error('Error fetching trending data:', err);
        setError('获取趋势数据失败，请稍后再试。');
      } finally {
        setLoading(false);
      }
    };

    fetchTrendingData();
  }, [selectedPlatform]);

  // 处理平台选择
  const handlePlatformChange = (platformId: string) => {
    setSelectedPlatform(platformId);
  };

  // 获取当前选中平台的数据
  const getCurrentPlatformData = () => {
    if (!selectedPlatform) return null;
    return trendingData.find(data => data.platform === selectedPlatform) || null;
  };

  // 获取所有平台的数据
  const getAllPlatformsData = () => {
    return trendingData;
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8 text-center">
          <motion.h1 
            className="text-4xl font-bold text-gray-800 dark:text-white mb-2"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            热门趋势聚合
          </motion.h1>
          <motion.p 
            className="text-lg text-gray-600 dark:text-gray-300"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            实时获取各大平台热门内容
          </motion.p>
        </header>

        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded shadow-md">
            <p>{error}</p>
          </div>
        )}

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden mb-8">
          <Tab.Group>
            <Tab.List className="flex p-1 space-x-1 bg-gray-100 dark:bg-gray-700">
              <Tab
                key="all"
                className={({ selected }) =>
                  `w-full py-2.5 text-sm font-medium leading-5 rounded-lg transition-all duration-200 ${
                    selected
                      ? 'bg-white dark:bg-gray-800 shadow text-blue-600 dark:text-blue-400'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-white/[0.12] hover:text-gray-700 dark:hover:text-gray-300'
                  }`
                }
                onClick={() => setSelectedPlatform('all')}
              >
                <div className="flex items-center justify-center">
                  <GlobeAltIcon className="w-5 h-5 mr-2" />
                  全部平台
                </div>
              </Tab>
              
              {platforms.map((platform) => (
                <Tab
                  key={platform.id}
                  className={({ selected }) =>
                    `w-full py-2.5 text-sm font-medium leading-5 rounded-lg transition-all duration-200 ${
                      selected
                        ? 'bg-white dark:bg-gray-800 shadow text-blue-600 dark:text-blue-400'
                        : 'text-gray-600 dark:text-gray-400 hover:bg-white/[0.12] hover:text-gray-700 dark:hover:text-gray-300'
                    }`
                  }
                  onClick={() => handlePlatformChange(platform.id)}
                >
                  {platform.name}
                </Tab>
              ))}
            </Tab.List>
            
            <Tab.Panels className="mt-2 p-4">
              <AnimatePresence mode="wait">
                {loading ? (
                  <div className="flex justify-center items-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                  </div>
                ) : selectedPlatform === 'all' ? (
                  <div className="space-y-8">
                    {getAllPlatformsData().map((platformData) => (
                      <motion.div 
                        key={platformData.platform}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.3 }}
                        className="mb-6"
                      >
                        <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white flex items-center">
                          <ArrowTrendingUpIcon className="w-5 h-5 mr-2 text-blue-500" />
                          {platformData.display_name}
                        </h2>
                        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                          <TrendingItemsList items={platformData.items} />
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <motion.div
                    key={selectedPlatform}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    {getCurrentPlatformData() ? (
                      <TrendingItemsList items={getCurrentPlatformData()!.items} />
                    ) : (
                      <div className="text-center py-10 text-gray-500 dark:text-gray-400">
                        没有找到数据
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </Tab.Panels>
          </Tab.Group>
        </div>
        
        <footer className="text-center text-gray-500 dark:text-gray-400 text-sm mt-12">
          <p>数据来源于各大平台，每5分钟更新一次</p>
          <p className="mt-1"> {new Date().getFullYear()} Trending Scraper</p>
        </footer>
      </div>
    </main>
  );
}

// 趋势项列表组件
function TrendingItemsList({ items }: { items: TrendingItem[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {items.map((item, index) => (
        <motion.div
          key={`${item.platform}-${item.rank}-${index}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200"
        >
          <div className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center">
                <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center">
                  <span className="mr-1">#{item.rank}</span>
                  {item.score && <span>· {item.score}</span>}
                </span>
                {item.category && (
                  <span className="ml-2 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs px-2.5 py-0.5 rounded-full">
                    {item.category}
                  </span>
                )}
              </div>
              {item.score && item.score > 0 && (
                <div className="flex items-center text-green-500">
                  <ArrowUpIcon className="w-4 h-4 mr-1" />
                  <span className="text-xs font-medium">{item.score}</span>
                </div>
              )}
            </div>
            
            <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white line-clamp-2">
              <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 dark:hover:text-blue-400">
                {item.title}
              </a>
            </h3>
            
            {item.description && (
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                {item.description}
              </p>
            )}
            
            <div className="mt-3 flex items-center justify-between">
              {item.author ? (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {item.author}
                </span>
              ) : (
                <span></span>
              )}
              
              {item.timestamp && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {new Date(item.timestamp).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
