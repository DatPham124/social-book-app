<script setup>
import { onMounted, ref } from 'vue';
import axios from 'axios';

const books = ref([]);

const errorMessages = ref("")

async function getBooks() {
    try {
        const response = await axios.get('http://localhost:8001/books/');
        books.value = response.data
    }
    catch (error) {
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
                {{ book.title }} - {{ book.authorID }}
                <img :src="`http://34.9.73.53/uploads/${book.cover_url}`" alt="Book Cover" />
            </li>

        </ul>
    </div>



</template>