import { ref, onUnmounted } from 'vue';
import { 
    doc, onSnapshot, setDoc, serverTimestamp, 
    collection, addDoc, query, orderBy, limit, onSnapshot as onCollectionSnapshot 
} from 'firebase/firestore'; 
// Đảm bảo đường dẫn này đúng với file config của bạn
import { db } from '../firebase'; 

export function useAudioSync() {
    const remoteCommand = ref<any>(null);
    
    // MỚI: Biến chứa cảm xúc vừa nhận được
    const incomingReaction = ref<{ type: string, id: string } | null>(null);

    let unsubscribeRoom: (() => void) | null = null;
    let unsubscribeReactions: (() => void) | null = null;

    const joinRoom = (roomId: string, currentUserId: number | string) => {
        leaveRoom();

        // 1. Lắng nghe Player State (Giữ nguyên)
        const docRef = doc(db, 'rooms', roomId, 'player', 'state');
        unsubscribeRoom = onSnapshot(docRef, (docSnap) => {
            if (docSnap.exists()) {
                const data = docSnap.data();
                if (String(data.updatedBy) === String(currentUserId)) return;
                remoteCommand.value = data;
            }
        });

        // 2. Lắng nghe Reactions (MỚI)
        // Chỉ lấy 1 reaction mới nhất thêm vào
        const reactionsRef = collection(db, 'rooms', roomId, 'reactions');
        const q = query(reactionsRef, orderBy('timestamp', 'desc'), limit(1));
        
        unsubscribeReactions = onCollectionSnapshot(q, (snapshot) => {
            snapshot.docChanges().forEach((change) => {
                if (change.type === "added") {
                    const data = change.doc.data();
                    // Cập nhật biến để View biết có reaction mới
                    incomingReaction.value = { type: data.type, id: change.doc.id };
                }
            });
        });
    };

    const leaveRoom = () => {
        if (unsubscribeRoom) unsubscribeRoom();
        if (unsubscribeReactions) unsubscribeReactions();
    };

    const sendControl = async (roomId: string, action: string, payload: any, userId: number | string) => {
        const docRef = doc(db, 'rooms', roomId, 'player', 'state');
        try {
            await setDoc(docRef, { action, payload, updatedBy: userId, timestamp: serverTimestamp() }, { merge: true });
        } catch (e) { console.error(e); }
    };

    // 3. Hàm gửi Reaction (MỚI)
    const sendReaction = async (roomId: string, type: string, userId: number | string) => {
        try {
            await addDoc(collection(db, 'rooms', roomId, 'reactions'), {
                type,
                userId,
                timestamp: serverTimestamp()
            });
        } catch (e) { console.error(e); }
    };

    onUnmounted(() => {
        leaveRoom();
    });

    return {
        remoteCommand,
        incomingReaction, // Export ra
        joinRoom,
        leaveRoom,
        sendControl,
        sendReaction      // Export ra
    };
}