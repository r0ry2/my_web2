
// عند الضغط على زر "Find your favorite"
document.getElementById("findFavoriteBtn").addEventListener("click", function () {
    document.getElementById("sectionـProduct").scrollIntoView({ behavior: "smooth" });
  });



  // زر العودة للأعلى
  const goToTopBtn = document.getElementById("goToTopBtn");

  
  // التحكم في ظهور زر العودة للأعلى بناءً على التمرير
  window.onscroll = function () {
    if (window.scrollY > 100) {// إذا تجاوز المستخدم 100 بكسل للأسفل، يتم إظهار الزر.

      goToTopBtn.style.display = "block";// يظهر الزر عندما يتم التمرير لأسفل.
    } else {
      goToTopBtn.style.display = "none";
    }
  };
  // عند الضغط على زر العودة للأعلى
  goToTopBtn.onclick = function () {//When the button is clicked, the code is executed.
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  


 


  // دالة لفتح أو غلق القائمة الجانبية
function toggleSidebar() {
  var sidebar = document.getElementById("sidebar");
  if (sidebar.style.right === "0px") {
    sidebar.style.right = "-250px"; // إخفاء القائمة
  } else {
    sidebar.style.right = "0px"; // إظهار القائمة
  }
}

  
//search
  document.getElementById("searchBtn").addEventListener("click", function() {
    let searchTerm = document.getElementById("search").value.toLowerCase();
    let sections = document.querySelectorAll("section"); // البحث في جميع الأقسام

    let found = false;
    sections.forEach(section => {
        if (section.innerText.toLowerCase().includes(searchTerm)) {
            section.scrollIntoView({ behavior: "smooth", block: "start" });
            found = true;
        }
    });

    if (!found) {
        alert("No matching section found!");
    }
});






  // تخزين قيم نموذج الاتصال
  document.getElementById("submitForm").addEventListener("click", function () {
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const message = document.getElementById("message").value;
    console.log("Name:", name, "Email:", email, "Message:", message);//يستخدم console.log لطباعة البيانات المدخلة في المتصفح (Developer Console).
    alert("Form submitted successfully!");
  });







document.addEventListener("DOMContentLoaded", function() {
  // استرجاع عدد الزيارات من localStorage
  let visitCount = localStorage.getItem("visitCount");

  // إذا كانت الزيارة الأولى أو غير موجودة في localStorage، ابدأ العد من 1
  if (!visitCount) {
      visitCount = 1;
  } else {
      visitCount = parseInt(visitCount) + 1; // زيادة العددإذا كان هناك عدد زيارات مسجل بالفعل، يتم تحويله إلى عدد (parseInt(visitCount)) وزيادته بمقدار 1.

  }

  // حفظ العدد المحدث في localStorage
  localStorage.setItem("visitCount", visitCount);

  // عرض العدد في الصفحة
  const visitorCountElem = document.getElementById("visitor-count");
  if (visitorCountElem) {//يتحقق مما إذا كان العنصر موجودًا في الصفحة (لمنع الأخطاء).

      visitorCountElem.textContent = `Number of visitors: ${visitCount}`;
  }
});











//إضافة المنتجات
let cart = JSON.parse(localStorage.getItem('cart')) || [];

document.querySelectorAll('.product-section').forEach(section => {
    const priceElement = section.querySelector("#product-price");
    const quantityElement = section.querySelector("#product-quantity");
    const totalElement = section.querySelector("#total-price");
    const deliveryPrice = 10.1;

    // 🔹 دالة للحصول على الكمية الحالية
    const getQuantity = () => parseInt(quantityElement.textContent);//يحصل على العدد الموجود داخل #product-quantity (كمية المنتج في الصفحة) ويحوّله إلى عدد صحيح (Integer).


    // 🔹 دالة لحساب السعر الإجمالي وتحديثه في الصفحة
    const updateTotalPrice = () => {
        const productPrice = parseFloat(priceElement.textContent);
        const quantity = getQuantity();
        const totalPrice = (productPrice * quantity) + deliveryPrice;
        totalElement.textContent = totalPrice.toFixed(1) + ' TUB';
    };

    // 🔹 دالة لإضافة المنتج إلى السلة
    const addToCart = () => {
        const name = section.dataset.name;//يحصل على اسم المنتج من data-name المخزن في عنصر الـ HTML.
        const quantity = getQuantity();
        const price = parseFloat(totalElement.textContent.split(' ')[0]);
        cart.push({ name, quantity, price });//إضافة المنتج إلى السلة:
        localStorage.setItem('cart', JSON.stringify(cart));
        alert(`Added ${quantity} of ${name} to cart at ${price.toFixed(1)} TUB`);//إظهار رسالة تأكيد للمستخدم
    };

    // 🔹 زيادة الكمية
    section.querySelector("#increase-quantity").addEventListener('click', () => {
        quantityElement.textContent = getQuantity() + 1;
        updateTotalPrice();
    });

    // 🔹 تقليل الكمية
    section.querySelector("#decrease-quantity").addEventListener('click', () => {
        if (getQuantity() > 1) {
            quantityElement.textContent = getQuantity() - 1;
            updateTotalPrice();
        }
    });

    // 🔹 زر الإضافة إلى السلة
    section.querySelector(".add-to-cart").addEventListener('click', addToCart);

    // تحديث السعر عند تحميل الصفحة
    updateTotalPrice();
});
