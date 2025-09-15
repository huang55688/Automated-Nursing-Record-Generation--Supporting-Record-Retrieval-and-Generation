console.log("input.js 已成功載入！");

document.addEventListener("DOMContentLoaded", function () {
    console.log("input.js loaded");

    /* === 0) 預設填入「當前日期、當前時間」(若 date/time 欄位是空的) === */
    const dateInput = document.querySelector('input[name="date"]');
    const timeInput = document.querySelector('input[name="time"]');
    
    // 如果 date 欄位沒有預設值，就自動填今天的日期
    if (dateInput && !dateInput.value) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');document.getElementById
        const day = String(today.getDate()).padStart(2, '0');
        dateInput.value = `${year}-${month}-${day}`;  // 格式: yyyy-MM-dd
    }
    
    // 如果 time 欄位沒有預設值，就自動填現在的時間
    if (timeInput && !timeInput.value) {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        timeInput.value = `${hours}:${minutes}`;
    }

    // 用於存放「View」事件載入的各種 Symptom 欄位
    window.currentSymData = "";
    window.currentSymAction = "";
    window.currentSymResponse = "";
    window.currentSymTeaching = "";

    /* === 1) 綁定 View 按鈕，載入病人資料 === */
    const viewButtons = document.querySelectorAll(".view-btn");
    viewButtons.forEach(function (button) {
        button.addEventListener("click", function (e) {
            e.preventDefault();
            const patientId = this.getAttribute("data-patient-id");
            console.log("View 按鈕被點擊，patientId:", patientId);

            fetch(`/get_latest_patient_data/${patientId}`)
                .then(response => {
                    console.log("收到回應，狀態:", response.status);
                    return response.json();
                })
                .then(data => {
                    console.log("後端傳回的資料:", data);
                    if (data.error) {
                        alert(data.error);
                    } else {
                        // 填入基本資料與 Vitals
                        document.getElementById("patient_id").value = data.patient_id;
                        document.querySelector('input[name="patient_name"]').value = data.patient_name;
                        if (data.gender === "girl") {
                            document.querySelector('input[name="gender"][value="girl"]').checked = true;
                        } else if (data.gender === "boy") {
                            document.querySelector('input[name="gender"][value="boy"]').checked = true;
                        }
                        document.querySelector('input[name="age"]').value = data.age;
                        document.querySelector('input[name="ward"]').value = data.ward_name;
                        document.querySelector('input[name="date"]').value = data.date;
                        // 使用當下時間覆蓋後端傳回的 time
                        const now = new Date();
                        const hours = String(now.getHours()).padStart(2, '0');
                        const minutes = String(now.getMinutes()).padStart(2, '0');
                        document.querySelector('input[name="time"]').value = `${hours}:${minutes}`;
                        const year  = now.getFullYear();
                        const month = String(now.getMonth() + 1).padStart(2, '0');
                        const day   = String(now.getDate()).padStart(2, '0');
                        document.querySelector('input[name="date"]').value = `${year}-${month}-${day}`;
                        document.querySelector('input[name="temperature"]').value = data.temperature;
                        document.querySelector('input[name="respiration"]').value = data.respiration;
                        document.querySelector('input[name="pulse"]').value = data.pulse;
                        document.querySelector('input[name="blood_pressure"]').value = data.blood_pressure;

                        // 將後端的 Symptom 欄位存到全域變數
                        window.currentSymData     = data.sym_data     || "";
                        window.currentSymAction   = data.sym_action   || "";
                        window.currentSymResponse = data.sym_response || "";
                        window.currentSymTeaching = data.sym_teaching || "";

                        // 組合初次顯示的 Symptom 文字（使用 <br> 分行）
                        const symptomStr = buildSymptomHTML(
                            window.currentSymData,
                            window.currentSymAction,
                            window.currentSymResponse,
                            window.currentSymTeaching
                        );
                        document.getElementById("symptomDetails").innerHTML = symptomStr;
                        

                        // 顯示 "Check Abnormalities" 按鈕
                        document.getElementById("checkAbnormalContainer").style.display = "block";
                    }
                })
                .catch(err => {
                    console.error("Error fetching data:", err);
                });
        });
    });

        /* === 2) 綁定 Check Abnormalities 按鈕 === */
    const checkAbnormalBtn = document.getElementById("checkAbnormalBtn");
    if (checkAbnormalBtn) {
    checkAbnormalBtn.addEventListener("click", function (e) {
        e.preventDefault();
        console.log("Generate Symptoms 按鈕被點擊");
        syncSymptomDivToVariables();

        // 取得表單上的生理數據
        const temperature   = document.getElementById("temperature").value;
        const pulse         = document.getElementById("pulse").value;
        const respiration   = document.getElementById("respiration").value;
        const bloodPressure = document.getElementById("blood_pressure").value;

        // ★ 新增：若欄位未填完就提示
        if (!temperature || !pulse || !respiration || !bloodPressure) {
        alert("請先填寫完整的體溫、脈搏、呼吸與血壓再產生症狀！");
        return;
        }

        // 呼叫後端做異常判斷
        fetch("/check_abnormalities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            temperature:   temperature,
            pulse:         pulse,
            respiration:   respiration,
            blood_pressure: bloodPressure
        })
        })
        .then(res => res.json())
        .then(data => {
            // 若有異常，把紅字標註接到 currentSymData 後面
            if (data.abnormalities) {
                // 1. 把畫面上正在編輯的內容同步回變數
                syncSymptomDivToVariables();
            
                // 2. 如果目前 Data 不空，就加紅字；如果空，就只放紅字
                const red = `<span style="color:red;">(${data.abnormalities})</span>`;
                window.currentSymData = window.currentSymData
                  ? `${window.currentSymData} ${red}`
                  : red;
            
                // 3. 用目前 A/R/T + 新的 Data 重新渲染畫面
                const updatedSymptomStr = buildSymptomHTML(
                    window.currentSymData,
                    window.currentSymAction,
                    window.currentSymResponse,
                    window.currentSymTeaching
                );
                document.getElementById("symptomDetails").innerHTML = updatedSymptomStr;
            }
        })
        .catch(err => {
            console.error("Error checking abnormalities:", err);
            alert("異常偵測失敗，請稍後重試！");
        });
    });
    }


    /* === 3) 表單送出前，同步 contenteditable div 的內容到 hidden input === */
    document.querySelector("form.ff").addEventListener("submit", function () {
        const symptomDivContent = document.getElementById("symptomDetails").innerHTML;
        document.getElementById("hidden_symptom").value = symptomDivContent;
        // 同步其他隱藏欄位
        document.getElementById("hidden_patient_id").value = document.getElementById("patient_id").value;
        document.getElementById("hidden_date").value = document.getElementById("date").value;
        document.getElementById("hidden_time").value = document.getElementById("time").value;
    });

/* === 小函式：組合 Symptom HTML === */
function buildSymptomHTML(d, a, r, t) {
    /* 只有 Data、其餘三欄皆空 ——> 直接回傳純內容 */
    if (!a && !r && !t) {
        return d ? `${d}` : "";
    }

    /* 至少有一欄 Action / Response / Teaching 時，照舊產生四列 */
    let html = "";
    if (d) html += `<p><span style="font-weight:bold;">Data:</span> ${d}</p>`;
    if (a) html += `<p><span style="font-weight:bold;">Action:</span> ${a}</p>`;
    if (r) html += `<p><span style="font-weight:bold;">Response:</span> ${r}</p>`;
    if (t) html += `<p><span style="font-weight:bold;">Teaching:</span> ${t}</p>`;
    return html;
}

/* === 把畫面內容同步回四個全域變數 === */
function syncSymptomDivToVariables() {
    const rawHTML = document.getElementById("symptomDetails").innerHTML;

    const getField = (label) => {
        const re = new RegExp(label + ':\\s*</span>\\s*([^<]*)', 'i');
        const m = rawHTML.match(re);
        return m ? m[1].trim() : "";
    };

    const maybeData     = getField('Data');
    const maybeAction   = getField('Action');
    const maybeResponse = getField('Response');
    const maybeTeaching = getField('Teaching');

    if (maybeData || maybeAction || maybeResponse || maybeTeaching) {
        // 目前內容是我們產生的標準格式
        window.currentSymData     = maybeData;
        window.currentSymAction   = maybeAction;
        window.currentSymResponse = maybeResponse;
        window.currentSymTeaching = maybeTeaching;
    } else {
        // 使用者自行輸入的純文字 => 全歸到 Data
        const plainText = document
            .getElementById("symptomDetails")
            .textContent.trim();
        if (plainText) {
            window.currentSymData = plainText;
            // Action / Response / Teaching 保持原值（或空）
        }
    }
}

});
