import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Login from "../views/Login.vue";
import Profile from "../views/Profile.vue";
import Book from "../views/Book.vue";

import EditProfile from "../components/profile/EditProfile.vue";
import Register from "../components/auth/RegisterForm.vue";
import ViewAllCurrentlyReadingBook from "../components/books/ViewAllCurrentlyReadingBook.vue";
import ViewAllReadBook from "../components/books/ViewAllReadBook.vue";
import ViewAllToReadBook from "../components/books/ViewAllToReadBook.vue";
import ReviewBook from "../components/books/ReviewBook.vue";
import ListReview from "../components/books/ListReview.vue";
import DetailReview from "../components/books/DetailReview.vue";

import Notification from "../views/Notification.vue";

import CommunityTab from "../views/CommunityTab.vue";
import BookClubCard from "../components/community/BookClub/BookClubCard.vue";
import MettingDetail from '../components/community/BookClub/MettingDetail.vue';

import DiscussionDetail from "../components/community/BookClub/DiscussionDetail.vue";

const routes = [
  { path: "/login", name: "Login", component: Login },
  { path: "/home", name: "Home", component: Home },
  { path: "/register", name: "register", component: Register },
  { path: "/profile/:id", name: "profile", component: Profile },

  { path: "/profile/edit", name: "edit_profilefile", component: EditProfile },
  {
    path: "/profile/view/curently",
    name: "view_currently_reading_book",
    component: ViewAllCurrentlyReadingBook,
  },
  {
    path: "/profile/view/read",
    name: "view_all_read_book",
    component: ViewAllReadBook,
  },
  {
    path: "/profile/view/toread",
    name: "view_all_to_read_book",
    component: ViewAllToReadBook,
  },
  { path: "/book/:id", name: "book", component: Book },
  { path: "/book/:id/review", name: "ReviewBook", component: ReviewBook },

  { path: "/book/:id/list-review", name: "ListReview", component: ListReview },

  {
    path: "/book/:bookId/review/:reviewId",
    name: "DetailReview",
    component: DetailReview,
  },

  {
    path: "/notifications",
    name: "Notification",
    component: Notification,
  },

  {
    path: "/community",
    name: "CommunityTab",
    component: CommunityTab,
  },

  {
    path: "/bookclub/:id",
    name: "BookClubCard",
    component: BookClubCard,
    props: true,
  },
  {
    path: '/meeting/:id', 
    name: 'MeetingDetail',
    component: MettingDetail,
    meta: { requiresAuth: true } 
  },

  {
    path: '/discussion/:id',
    name: 'DiscussionDetail',
    component: DiscussionDetail,
    meta: { requiresAuth: true }
  },

  { path: "/", redirect: "/login" },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
