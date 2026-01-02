<script setup lang="ts">
import Navbar from '../components/layout/Navbar.vue';
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { BOOK_SERVICE_URL } from '../config'; 

// Import Chart.js components
import { Bar, Pie } from 'vue-chartjs';
import { 
  Chart as ChartJS, 
  Title, 
  Tooltip, 
  Legend, 
  BarElement, 
  CategoryScale, 
  LinearScale,
  ArcElement 
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  Title, 
  Tooltip, 
  Legend, 
  BarElement, 
  CategoryScale, 
  LinearScale,
  ArcElement 
);

const route = useRoute();
const userId = route.params.id;

// Tách riêng loading cho từng khối
const loadingKpis = ref(true); 
const loadingMonthlyChart = ref(true); 
const loadingPageChart = ref(true);
const loadingCategoryChart = ref(true);
const loadingAuthorChart = ref(true); // MỚI: Loading cho biểu đồ tác giả
const error = ref<string | null>(null);

// Ref cho KPIs (và biểu đồ kệ sách)
const kpiStats = ref({
  total_read: 0,
  total_pages: 0,
  avg_time_to_finish: 0.0,
  read_this_year: 0,
  favorites_count: 0,
  clubs_count: 0,
  shelf_counts: {
    to_read: 0,
    currently_reading: 0,
    read: 0,
    dnf: 0,
  },
});

// Ref cho biểu đồ tháng
const monthlyData = ref<number[]>([]);
// Ref cho biểu đồ độ dài sách
const pageDistData = ref({
  short: 0,
  medium: 0,
  long: 0,
});
// Ref cho biểu đồ thể loại
const categoryData = ref<{ name: string, count: number }[]>([]);
// MỚI: Ref cho biểu đồ tác giả
const authorData = ref<{ name: string, count: number }[]>([]);

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('en-US').format(num);
};

// --- CÁC HÀM TẢI DỮ LIỆU ---

async function loadKpiStats() {
  if (!userId) {
    error.value = "Không tìm thấy ID người dùng.";
    loadingKpis.value = false;
    return;
  }
  loadingKpis.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}stats/kpis/${userId}`);
    kpiStats.value = res.data;
  } catch (err) {
    console.error(err);
    error.value = "Không thể tải dữ liệu thống kê KPIs.";
  } finally {
    loadingKpis.value = false;
  }
}

async function loadMonthlyStats() {
  if (!userId) {
    loadingMonthlyChart.value = false;
    return;
  }
  loadingMonthlyChart.value = true;
  try {
    const currentYear = new Date().getFullYear();
    const res = await axios.get(`${BOOK_SERVICE_URL}stats/read-by-month/${userId}`, {
      params: { year: currentYear }
    });
    monthlyData.value = res.data.data;
  } catch (err) {
    console.error(err);
    if (!error.value) error.value = "Không thể tải dữ liệu biểu đồ tháng.";
  } finally {
    loadingMonthlyChart.value = false;
  }
}

async function loadPageStats() {
  if (!userId) {
    loadingPageChart.value = false;
    return;
  }
  loadingPageChart.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}stats/page-distribution/${userId}`);
    pageDistData.value = res.data;
  } catch (err) {
    console.error(err);
    if (!error.value) error.value = "Không thể tải dữ liệu biểu đồ độ dài sách.";
  } finally {
    loadingPageChart.value = false;
  }
}

async function loadTopCategories() {
  if (!userId) {
    loadingCategoryChart.value = false;
    return;
  }
  loadingCategoryChart.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}stats/top-categories/${userId}`);
    categoryData.value = res.data;
  } catch (err) {
    console.error(err);
    if (!error.value) error.value = "Không thể tải dữ liệu top thể loại.";
  } finally {
    loadingCategoryChart.value = false;
  }
}

// MỚI: Hàm tải Top 5 Tác giả
async function loadTopAuthors() {
  if (!userId) {
    loadingAuthorChart.value = false;
    return;
  }
  loadingAuthorChart.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}stats/top-authors/${userId}`);
    authorData.value = res.data;
  } catch (err) {
    console.error(err);
    if (!error.value) error.value = "Không thể tải dữ liệu top tác giả.";
  } finally {
    loadingAuthorChart.value = false;
  }
}


// Load tất cả khi mounted
onMounted(() => {
  loadKpiStats();
  loadMonthlyStats();
  loadPageStats();
  loadTopCategories(); 
  loadTopAuthors(); // <-- Gọi hàm mới
});

// --- CẤU HÌNH BIỂU ĐỒ ---

// Cấu hình Biểu đồ CỘT (Bar Chart)
const isMonthlyDataEmpty = computed(() => {
  return monthlyData.value.every(count => count === 0);
});

const barChartData = computed(() => {
  return {
    labels: [
      'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 
      'T7', 'T8', 'T9', 'T10', 'T11', 'T12'
    ],
    datasets: [
      {
        label: 'Số sách đọc',
        backgroundColor: '#fde047', 
        borderColor: '#facc15',   
        borderWidth: 1,
        borderRadius: 4,
        data: monthlyData.value, 
      },
    ],
  };
});

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#111827', 
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { precision: 0 },
      grid: { drawBorder: false, color: '#e5e7eb' },
    },
    x: {
      grid: { display: false },
    },
  },
};

// Cấu hình Biểu đồ TRÒN (Kệ sách)
const isShelfDataEmpty = computed(() => {
  const counts = kpiStats.value.shelf_counts;
  return counts.read === 0 && counts.to_read === 0 && counts.currently_reading === 0 && counts.dnf === 0;
});

const pieChartData = computed(() => {
  const counts = kpiStats.value.shelf_counts;
  return {
    labels: [ 'Muốn đọc', 'Đang đọc', 'Đã đọc', 'Bỏ dở (DNF)' ],
    datasets: [
      {
        backgroundColor: [ '#60a5fa', '#fbbf24', '#34d399', '#f87171' ],
        borderColor: '#ffffff', 
        borderWidth: 2,
        data: [ counts.to_read, counts.currently_reading, counts.read, counts.dnf ]
      }
    ]
  };
});

const pieChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const, 
      labels: { boxWidth: 12, font: { size: 14 }, padding: 20 }
    },
    tooltip: {
      backgroundColor: '#111827',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
    },
  }
};

// Cấu hình Biểu đồ TRÒN (Độ dài Sách)
const isPageDataEmpty = computed(() => {
  const counts = pageDistData.value;
  return counts.short === 0 && counts.medium === 0 && counts.long === 0;
});

const pageChartData = computed(() => {
  const counts = pageDistData.value;
  return {
    labels: [
      'Dưới 300 trang', 
      '300 - 499 trang', 
      '500+ trang'
    ],
    datasets: [
      {
        backgroundColor: [ 
          '#a78bfa', // Violet-400
          '#f472b6', // Pink-400
          '#22d3ee'  // Cyan-400
        ], 
        borderColor: '#ffffff', 
        borderWidth: 2,
        data: [ counts.short, counts.medium, counts.long ]
      }
    ]
  };
});

const pageChartOptions = pieChartOptions;

// Cấu hình Biểu đồ NGANG (Top Thể loại)
const categoryChartData = computed(() => {
  return {
    labels: categoryData.value.map(item => item.name), // ["Lãng mạn", "Trinh thám", ...]
    datasets: [
      {
        label: 'Số sách đọc',
        backgroundColor: '#818cf8', // Indigo-400
        borderColor: '#6366f1',
        borderWidth: 1,
        borderRadius: 4,
        data: categoryData.value.map(item => item.count), // [10, 8, ...]
      },
    ],
  };
});

const categoryChartOptions = {
  indexAxis: 'y' as const, 
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#111827', 
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
    },
  },
  scales: {
    y: {
      grid: { display: false },
    },
    x: {
      beginAtZero: true,
      ticks: { precision: 0 },
      grid: { drawBorder: false, color: '#e5e7eb' },
    },
  },
};

// MỚI: Cấu hình Biểu đồ NGANG (Top Tác giả)
const authorChartData = computed(() => {
  return {
    labels: authorData.value.map(item => item.name),
    datasets: [
      {
        label: 'Số sách đọc',
        backgroundColor: '#fb923c', // Orange-400
        borderColor: '#f97316',
        borderWidth: 1,
        borderRadius: 4,
        data: authorData.value.map(item => item.count),
      },
    ],
  };
});

// (Có thể dùng chung options với category)
const authorChartOptions = categoryChartOptions;

</script>

<template>
  <Navbar />

  <div class="w-full max-w-5xl mx-auto m-5 space-y-6 px-4">
    <h1 class="text-2xl font-logo text-yellow-400 item-center">Thống kê</h1>

    <!-- Khối loading/error chính -->
    <div v-if="loadingKpis" class="text-center text-gray-500 py-10">
      Đang tải số liệu...
    </div>

    <div v-else-if="error" class="text-center text-red-500 py-10">
      {{ error }}
    </div>

    <!-- Khối hiển thị dữ liệu -->
    <div v-else class="space-y-8">

      <!-- Khối "Read" (Đã đọc) -->
      <div class="bg-white p-6 rounded-lg shadow border border-gray-200">
        
        <h3 class="text-xl font-semibold text-gray-800 text-center border-b pb-3">
          Đã đọc
        </h3>

        <div class="text-center pt-4">
          
          <p class="text-md text-gray-600">
            {{ formatNumber(kpiStats.total_read) }} sách, 
            {{ formatNumber(kpiStats.total_pages) }} trang
          </p>

          <p class="text-sm text-gray-500 mt-4">
            Thời gian đọc trung bình
          </p>
          <p class="text-5xl font-bold text-teal-600 mt-1">
            {{ Math.round(kpiStats.avg_time_to_finish) }} ngày
          </p>

          <p class="text-sm text-gray-500 mt-4">
            Sách đọc trong năm nay
          </p>
          <p class="text-3xl font-bold text-teal-500 mt-1">
             {{ formatNumber(kpiStats.read_this_year) }}
          </p>
          
        </div>
      </div>
      
      <!-- Khối: Biểu đồ tháng -->
      <div class="bg-white p-6 rounded-lg shadow border border-gray-200">
        
        <h3 class="text-xl font-semibold text-gray-800 text-center border-b pb-3">
          Sách đọc theo tháng ({{ new Date().getFullYear() }})
        </h3>
        
        <div class="pt-4">
          <div v-if="loadingMonthlyChart" class="text-center text-gray-500 py-10">
            Đang tải biểu đồ...
          </div>
          <div v-else-if="isMonthlyDataEmpty" class="text-center text-gray-500 py-10 italic">
            Chưa có dữ liệu đọc sách trong năm nay.
          </div>
          <div v-else style="height: 300px">
            <Bar :data="barChartData" :options="barChartOptions" />
          </div>
        </div>
        
      </div>

      <!-- Khối Biểu đồ ngang Top Thể loại -->
      <div class="bg-white p-6 rounded-lg shadow border border-gray-200">
        
        <h3 class="text-xl font-semibold text-gray-800 text-center border-b pb-3">
          Top 5 Thể loại
        </h3>
        
        <div class="pt-4">
          <div v-if="loadingCategoryChart" class="text-center text-gray-500 py-10">
            Đang tải biểu đồ...
          </div>
          <div v-else-if="categoryData.length === 0" class="text-center text-gray-500 py-10 italic">
            Bạn chưa đọc sách nào có gắn thẻ thể loại.
          </div>
          <div v-else :style="{ height: (categoryData.length * 50) + 'px' }">
            <Bar :data="categoryChartData" :options="categoryChartOptions" />
          </div>
        </div>
        
      </div>

      <!-- MỚI: Khối Biểu đồ ngang Top Tác giả -->
      <div class="bg-white p-6 rounded-lg shadow border border-gray-200">
        
        <h3 class="text-xl font-semibold text-gray-800 text-center border-b pb-3">
          Top 5 Tác giả
        </h3>
        
        <div class="pt-4">
          <div v-if="loadingAuthorChart" class="text-center text-gray-500 py-10">
            Đang tải biểu đồ...
          </div>
          <div v-else-if="authorData.length === 0" class="text-center text-gray-500 py-10 italic">
            Bạn chưa đọc sách nào để thống kê tác giả.
          </div>
          <div v-else :style="{ height: (authorData.length * 50) + 'px' }">
            <Bar :data="authorChartData" :options="authorChartOptions" />
          </div>
        </div>
        
      </div>
      
      <!-- Khối: Biểu đồ tròn Kệ sách -->
      <div class="bg-white p-6 rounded-lg shadow border border-gray-200">
        
        <h3 class="text-xl font-semibold text-gray-800 text-center border-b pb-3">
          Phân bổ Kệ sách
        </h3>
        
        <div class="pt-4">
          <div v-if="isShelfDataEmpty" class="text-center text-gray-500 py-10 italic">
            Bạn chưa thêm sách nào vào kệ.
          </div>
          <div v-else style="height: 350px" class="flex justify-center items-center">
            <Pie :data="pieChartData" :options="pieChartOptions" />
          </div>
        </div>
        
      </div>
      
      <!-- Khối Biểu đồ tròn Độ dài Sách -->
      <div class="bg-white p-6 rounded-lg shadow border border-gray-200">
        
        <h3 class="text-xl font-semibold text-gray-800 text-center border-b pb-3">
          Phân bổ Độ dài Sách
        </h3>
        
        <div class="pt-4">
          <div v-if="loadingPageChart" class="text-center text-gray-500 py-10">
            Đang tải biểu đồ...
          </div>
          <div v-else-if="isPageDataEmpty" class="text-center text-gray-500 py-10 italic">
            Chưa có dữ liệu về độ dài sách đã đọc.
          </div>
          <div v-else style="height: 350px" class="flex justify-center items-center">
            <Pie :data="pageChartData" :options="pageChartOptions" />
          </div>
        </div>
        
      </div>

    </div>
  </div>
</template>