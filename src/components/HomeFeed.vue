<script setup>
import { onMounted, ref } from 'vue';
import axios from 'axios';

const books = ref([]);

const errorMessages = ref("")

async function getBooks() {
    try {
        const response = await axios.get('http://localhost:8001/books/');
        const updatedBooks = await Promise.all(
            response.data.map(async (book) => {
                const authorResponse = await getAuthor(book.authorID);
                const categoryResponse = await getCategory(book.categoryID);
                return { ...book, authorName: authorResponse.name, categoryName: categoryResponse.name};
            })
        );
        books.value = updatedBooks;
        return books.value;

    }
    catch (error) {
        if (axios.isAxiosError(error) && error.response) {
            errorMessages.value = error.response.data.detail;
        } else {
            errorMessages.value = "Không thể kết nối đến server";
        }
    }
}

async function getAuthor(authorID) {
    try {
        const response = await axios.get(`http://localhost:8001/author/${authorID}`);
        return response.data
    } catch (error) {
        if (axios.isAxiosError(error) && error.response) {
            errorMessages.value = error.response.data.detail;
        } else {
            errorMessages.value = "Không thể kết nối đến server";
        }
    }
}

async function getCategory(categoryID) {
    try {
        const response = await axios.get(`http://localhost:8001/category/${categoryID}`);
        return response.data
    } catch (error) {
        if (axios.isAxiosError(error) && error.response) {
            errorMessages.value = error.response.data.detail;
        } else {
            errorMessages.value = "Không thể kết nối đến server";
        }
    }
}


onMounted(() => {
    getBooks()
});

</script>

<template>

    <div>
        <div v-if="errorMessages"> {{ errorMessages }} </div>

        <ul v-else>

            <li v-for="book in books" :key="book.id">
                <div class="flex flex-row relative h-60 w-full bg-white rounded-lg shadow-md m-2">
                    <div class="relative h-full max-w-41">
                        <img :src="`http://34.9.73.53/uploads/${book.cover_url}`" alt="Book Cover"
                            class="h-full object-contain" />
                    </div>
                    <div class="m-4">
                        <p class="font-bold text-2xl">{{ book.title }}</p>
                        <p class="text-gray-600 mt-2">Tác giả: {{ book.authorName }}</p>
                        <p class="text-gray-600 mt-2">Thể loại: {{ book.categoryName }}</p>
                        <p class="text-gray-600 mt-2">Năm xuất bản: {{ book.published_date }}</p>
                        <p class="text-gray-600 mt-2">Mô tả: {{ book.description }}</p>
                    </div>
                </div>
            </li>

        </ul>
    </div>



</template>
