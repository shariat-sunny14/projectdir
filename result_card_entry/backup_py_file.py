@csrf_exempt
@login_required()
def annualResultsCardReportsManagerAPI(request):
    if request.method != 'POST':
        return HttpResponse("Invalid request")

    import json
    from django.template.loader import render_to_string

    print_blocks = request.POST.get("print_blocks")

    try:
        blocks = json.loads(print_blocks)
    except:
        return HttpResponse("Invalid JSON")

    rendered_pages = []

    for block in blocks:

        org_id = block.get("org_id")
        branch_id = block.get("branch_id")
        class_id = block.get("class_id")
        shift_id = block.get("shift_id")
        groups_id = block.get("groups_id")
        is_year = block.get("is_year")
        is_version = block.get("is_version")
        merit_id = block.get("merit_id")
        reg_ids = block.get("reg_ids", [])
        section_ids = block.get("section_ids", [])

        # version detect
        is_english = True if is_version == "english" else False
        is_bangla = True if is_version == "bangla" else False

        # ================================
        # Fetch all merit positions for given merit_id at once
        # ================================
        merit_qs = in_merit_position_approvaldtls.objects.filter(
            merit_id=merit_id,
            reg_id__in=reg_ids
        ).values("reg_id", "merit_position")

        merit_dict = {item["reg_id"]: item["merit_position"]
            for item in merit_qs}

        # Sort reg_ids by merit_position ascending
        reg_ids_sorted = sorted(
            reg_ids, key=lambda rid: merit_dict.get(rid, float('inf'))
        )

        for reg_id in reg_ids_sorted:

            merit_position = merit_dict.get(reg_id, 0)

            # ================================
            # FILTER RESULT CARD ENTRY
            # ================================
            card_entry = in_results_card_entry.objects.filter(
                reg_id=reg_id,
                org_id=org_id,
                branch_id=branch_id,
                class_id=class_id,
                shift_id=shift_id,
                groups_id=groups_id,
                is_annual=True if is_year else False,
            ).first()

            if not card_entry:
                return HttpResponse(
                    f"No result card found for RegID={reg_id}",
                )

            registration = card_entry.reg_id

            # =================================
            # Collect Grade Maps
            # =================================
            fifty_grades = in_letter_gradeFiftyMap.objects.filter(
                is_active=True, org_id=org_id, class_id=class_id)
            hundred_grades = in_letter_gradeHundredMap.objects.filter(
                is_active=True, org_id=org_id, class_id=class_id)

            if is_english:
                fifty_grades = fifty_grades.filter(is_english=True)
                hundred_grades = hundred_grades.filter(is_english=True)
            if is_bangla:
                fifty_grades = fifty_grades.filter(is_bangla=True)
                hundred_grades = hundred_grades.filter(is_bangla=True)

            fifty_grade_ids = list(
                fifty_grades.values_list("grade_id", flat=True))
            hundred_grade_ids = list(
                hundred_grades.values_list("grade_id", flat=True))
            grade_ids = set(fifty_grade_ids + hundred_grade_ids)

            grades = in_letter_grade_mode.objects.filter(
                grade_id__in=grade_ids
            ).order_by("grade_id")

            # ===============================
            # Table Data Prepare
            # ===============================
            table_data = []
            for grade in grades:
                fifty_map = fifty_grades.filter(grade_id=grade).first()
                hundred_map = hundred_grades.filter(grade_id=grade).first()
                table_data.append({
                    "grade_name": grade.is_grade_name,
                    "fifty_interval": f"{fifty_map.from_marks}-{fifty_map.to_marks}" if fifty_map else "",
                    "hundred_interval": f"{hundred_map.from_marks}-{hundred_map.to_marks}" if hundred_map else "",
                    "grade_point": fifty_map.grade_point if fifty_map else (hundred_map.grade_point if hundred_map else "")
                })

            # ===============================
            # Transaction Data
            # ===============================
            def title_case(value):
                return ' '.join(word.capitalize() for word in value.split()) if value else ''

            transaction = {
                'create_date': card_entry.create_date or '',
                'reg_id': registration.reg_id if registration else '',
                'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
                'full_name': title_case(registration.full_name),
                'roll_no': registration.roll_no or '',
                'father_name': title_case(registration.father_name),
                'mother_name': title_case(registration.mother_name),
                'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
                'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
                'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
                'total_working_days': card_entry.total_working_days or '',
                'total_present_days': card_entry.total_present_days or '',
                'is_remarks': card_entry.is_remarks or '',
                'date_of_publication': card_entry.date_of_publication or '',
                'is_average_gpa': card_entry.is_average_gpa or '',
                'average_letter_grade': card_entry.average_letter_grade or '',
                'total_obtained_marks': card_entry.total_obtained_marks or '',
                'result_status': card_entry.result_status or '',
                'merit_position': merit_position,
                'is_year': is_year,
            }

            html = render_to_string(
                'result_card_entry/annual_result_card/annual_card_report/annual_report_card_report.html',
                {
                    "transaction": transaction,
                    "registration": registration,
                    "table_data": table_data,
                }
            )

            rendered_pages.append(html)

    return HttpResponse("".join(rendered_pages))


<script >
        $(document).ready(function() {
            if (window._annualResultsLoaded) return ;
            window._annualResultsLoaded= true;

            var org_id= $('#id_is_org_id').val();
            var branch_id= $('#id_is_branch_id').val();
            var class_id= $('#id_is_class_id').val();
            var shift_id= $('#id_is_shifts_id').val();
            var groups_id= $('#id_is_groups_id').val();
            var isEnglish= $('#id_is_english_id').val();
            var isBangla= $('#id_is_bangla_id').val();
            var year= $('#id_is_year').val();

            var reg_ids = $("input[name='is_reg_id[]']").map(function(){return $(this).val(); }).get();

            var version= (isEnglish == 'True' | | isEnglish == '1')
                    ? 'english': (isBangla == 'True' | | isBangla == '1')
                        ? 'bangla': 'english';

            function fmt(v) {
                v= Number(v ?? 0);
                return (v % 1 === 0) ? parseInt(v): v.toFixed(2);
            }

            $.ajax({
                url: "/print_is_annual_details_result/",
                type: "GET",
                traditional: true,
                data: {
                    org_id: org_id,
                    branch_id: branch_id,
                    reg_ids: reg_ids,
                    class_id: class_id,
                    shift_id: shift_id,
                    groups_id: groups_id,
                    is_year: year,
                    is_version: version
                },
                success: function(response) {
                    const regKeys= Object.keys(response);
                    if (regKeys.length == = 0) {
                        alert("No data found!");
                        return ;
                    }

                    const $table= $("#ANNUALCARDREPORT");
                    $table.find("thead").html(""); // clear previous header
                    $table.find("tbody").html(""); // clear previous body

                    regKeys.forEach(reg_id=> {
                        const data= response[reg_id];
                        if (!data.success) return ;

                        const modeNames= data.mode_names;
                        const subjects= data.final_subjects;

                        // Build header only once(for first reg_id)
                        if ($table.find("thead"). is (":empty")) {
                            let headerHTML = ` < tr >
                                < th rowspan= "2" style = "text-align:center; border:1px solid #24326a; width:20%;" > Name of Subjects < /th >
                                < th rowspan= "2" style = "text-align:center; border:1px solid #24326a; writing-mode:vertical-rl; transform: rotate(180deg); white-space:nowrap;" > Full Marks < /th >
                                < th colspan= "${modeNames.length +1}" style = "text-align:center; border:1px solid #24326a;" > Half Yearly Exam < /th >
                                < th colspan= "${modeNames.length +1}" style = "text-align:center; border:1px solid #24326a;" > Annual Exam < /th >
                                < th colspan = "${modeNames.length}" style = "text-align:center; border:1px solid #24326a;" > ${data.half_percent} % of Half Yearly Exam < /th >
                                < th colspan = "${modeNames.length}" style = "text-align:center; border:1px solid #24326a;" > ${data.annual_percent} % of Annual Exam < /th >
                                < th colspan= "${modeNames.length}" style = "text-align:center; border:1px solid #24326a;" > Total Particular Marks < /th >
                                < th rowspan= "2" style = "padding:5px; text-align:center; border:1px solid #24326a;" > Total Obtained Marks (Subject Wise) < /th >
                                < th rowspan= "2" style = "padding:5px; text-align:center; border:1px solid #24326a;" > Letter Grade < /th >
                                < th rowspan= "2" style = "width:4%; text-align:center; border:1px solid #24326a;" > GP < /th >
                            < / tr >
                            < tr >
                                ${modeNames.map(m=> ` < th style="padding:7px;text-align:center;border:1px solid #24326a;writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;" > ${m} < /th > `).join('')}
                                < th style= "padding:7px;text-align:center;border:1px solid #24326a;font-weight:bold;writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;" > Total < /th >
                                ${modeNames.map(m=> ` < th style="padding:7px;text-align:center;border:1px solid #24326a;writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;" > ${m} < /th > `).join('')}
                                < th style= "padding:7px;text-align:center;border:1px solid #24326a;font-weight:bold;writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;" > Total < /th >
                                ${modeNames.map(m=> ` < th style="padding:7px;text-align:center;border:1px solid #24326a;writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;" > ${m} < /th > `).join('')}
                                ${modeNames.map(m=> ` < th style="padding:7px;text-align:center;border:1px solid #24326a;writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;" > ${m} < /th > `).join('')}
                                ${modeNames.map(m=> ` < th style="padding:7px;text-align:center;border:1px solid #24326a;writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;" > ${m} < /th > `).join('')}
                            < /tr > `;
                            $table.find("thead").append(headerHTML);
                        }

                        let grandTotalFull= 0;
                        let grandTotalObtained= 0;

                        subjects.forEach(sub=> {
                            let halfTotal= 0;
                            let annualTotal= 0;
                            let finalTotal= 0;

                            let rowHTML = ` < tr >
                                < td style= "text-align:left; border:1px solid #ccc;" > ${sub.name}${sub.is_optional ? " (Optional)": sub.is_not_countable ? " (Not Countable)": ""} < /td >
                                < td style = "text-align:center; border:1px solid #ccc;" > ${fmt(sub.full_marks)} < /td > `;

                            modeNames.forEach(mode=> {
                                const v= Number(sub.modes[mode]?.half_actual ?? 0);
                                halfTotal += v;
                                rowHTML += ` < td style= "text-align:center; border:1px solid #ccc;" > ${fmt(v)} < /td > `;
                            });
                            rowHTML += ` < td style= "text-align:center; font-weight:bold; border:1px solid #ccc;" > ${fmt(halfTotal)} < /td > `;

                            modeNames.forEach(mode=> {
                                const v= Number(sub.modes[mode]?.annual_actual ?? 0);
                                annualTotal += v;
                                rowHTML += ` < td style= "text-align:center; border:1px solid #ccc;" > ${fmt(v)} < /td > `;
                            });
                            rowHTML += ` < td style= "text-align:center; font-weight:bold; border:1px solid #ccc;" > ${fmt(annualTotal)} < /td > `;

                            modeNames.forEach(mode=> {
                                rowHTML += ` < td style= "text-align:center; border:1px solid #ccc;" > ${fmt(sub.modes[mode]?.["40% of Half Yearly Exam"] ?? 0)} < /td > `;
                            });
                            modeNames.forEach(mode=> {
                                rowHTML += ` < td style= "text-align:center; border:1px solid #ccc;" > ${fmt(sub.modes[mode]?.["60% of Annual Exam"] ?? 0)} < /td > `;
                            });
                            modeNames.forEach(mode=> {
                                const v= Number(sub.modes[mode]?.["Total mode_names Marks"] ?? 0);
                                finalTotal += v;
                                rowHTML += ` < td style= "text-align:center; font-weight:bold; border:1px solid #ccc;" > ${fmt(v)} < /td > `;
                            });

                            rowHTML += ` < td style = "text-align:center; font-weight:bold; border:1px solid #ccc;" > ${fmt(finalTotal)} < /td >
                                < td style= "text-align:center; border:1px solid #ccc;" > ${sub.letter_grade} < /td >
                                < td style= "text-align:center; border:1px solid #ccc;" > ${sub.gp} < /td >
                            < / tr > `;

                            $table.find("tbody").append(rowHTML);

                            grandTotalFull += sub.full_marks;
                            grandTotalObtained += finalTotal;
                        });

                        // Add grand total row per reg_id
                        $table.find("tbody").append(` < tr style="font-weight:bold;" >
                            < td style="text-align:right; border:1px solid #ccc;" > Total Marks: < /td >
                            < td style="text-align:center; border:1px solid #ccc;" > ${fmt(grandTotalFull)} < /td >
                            < td colspan="${modeNames.length +1 + modeNames.length +1 + (modeNames.length *3)}" style="border:1px solid #ccc;" > </td >
                            < td style="text-align:center; border:1px solid #ccc;" > ${fmt(grandTotalObtained)} < /td >
                            < td style="border:1px solid #ccc;" > </td >
                            < td style="border:1px solid #ccc;" > </td >
                        < / tr > `);
                    });
                },
                error: function() {
                    alert("Error loading results.");
                }
            });
        });

    </script>





$(document).ready(function () {
            // get reg_id safely
            var org_id     = $('#id_is_org_id').val();
            var branch_id  = $('#id_is_branch_id').val();
            var reg_id     = $('#id_is_reg_id').val();        // array support
            var class_id   = $('#id_is_class_id').val();
            var section_id = $('#id_is_section_id').val();
            var shift_id   = $('#id_is_shifts_id').val();
            var groups_id  = $('#id_is_groups_id').val();
            var isEnglish  = $('#id_is_english_id').val();
            var isBangla   = $('#id_is_bangla_id').val();
            var year       = $('#id_is_year').val();
            //var reg_ids = $("input[name='is_reg_id[]']")
            //        .map(function(){ return $(this).val(); })
            //        .get();

            // Decide version
            var version = '';
            if (isEnglish == 'True' || isEnglish == 'true' || isEnglish == '1') {
                version = 'english';
            } else if (isBangla == 'True' || isBangla == 'true' || isBangla == '1') {
                version = 'bangla';
            } else {
                version = 'english'; // default fallback
            }

            loadIsAnnualResults(org_id, branch_id, reg_id, class_id, shift_id, groups_id, year, version);
            
            function loadIsAnnualResults(org_id, branch_id, reg_id, class_id, shift_id, groups_id, year, version) {

                // Number formatter
                function fmt(v) {
                    v = Number(v ?? 0);
                    return (v % 1 === 0) ? parseInt(v) : v.toFixed(2);
                }

                $.ajax({
                    url: "/get_is_annual_details_result_api/",
                    type: "GET",
                    data: {
                        org_id: org_id,
                        branch_id: branch_id,
                        reg_id: reg_id,
                        class_id: class_id,
                        shift_id: shift_id,
                        groups_id: groups_id,
                        is_year: year,
                        is_version: version
                    },
                    success: function (response) {

                        if (!response.success) {
                            toastr.error(response.message || "No data found!");
                            return;
                        }

                        const modeNames = response.mode_names;
                        const subjects = response.final_subjects;

                        // ===================================
                        // HEADER BUILD
                        // ===================================
                        let thead = `
                            <tr>
                                <th rowspan="2" style="text-align:center; border:1px solid #24326a; width:20%;">Name of Subjects</th>
                                <th rowspan="2" style="text-align:center; border:1px solid #24326a; writing-mode:vertical-rl; transform: rotate(180deg); white-space:nowrap;">Full Marks</th>

                                <th colspan="${modeNames.length + 1}" style="text-align:center; border:1px solid #24326a;">Half Yearly Exam</th>
                                <th colspan="${modeNames.length + 1}" style="text-align:center; border:1px solid #24326a;">Annual Exam</th>
                                <th colspan="${modeNames.length}" style="text-align:center; border:1px solid #24326a;">${response.half_percent}% of Half Yearly Exam</th>
                                <th colspan="${modeNames.length}" style="text-align:center; border:1px solid #24326a;">${response.annual_percent}% of Annual Exam</th>
                                <th colspan="${modeNames.length}" style="text-align:center; border:1px solid #24326a;">Total Particular Marks</th>

                                <th rowspan="2" style="padding: 5px;text-align:center; border:1px solid #24326a;">Total Obtained Marks (Subject Wise)</th>
                                <th rowspan="2" style="padding: 5px;text-align:center; border:1px solid #24326a;">Letter Grade</th>
                                <th rowspan="2" style="width: 4%; text-align:center; border:1px solid #24326a;">GP</th>
                            </tr>

                            <tr>
                                ${modeNames.map(m => `<th style="padding: 7px;text-align: center; border:1px solid #24326a; writing-mode:vertical-rl; transform: rotate(180deg); white-space:nowrap;">${m}</th>`).join("")}
                                <th style="padding: 7px;text-align: center; border:1px solid #24326a; font-weight:bold; writing-mode:vertical-rl; transform: rotate(180deg); white-space:nowrap;">Total</th>

                                ${modeNames.map(m => `<th style="padding: 7px;text-align: center; border:1px solid #24326a; writing-mode:vertical-rl; transform: rotate(180deg); white-space:nowrap;">${m}</th>`).join("")}
                                <th style="padding: 7px;text-align: center; border:1px solid #24326a; font-weight:bold; writing-mode:vertical-rl; transform: rotate(180deg); white-space:nowrap;">Total</th>
                                ${modeNames.map(m => `<th style="padding: 7px;text-align: center; border:1px solid #24326a; writing-mode:vertical-rl; transform: rotate(180deg); white-space:nowrap;">${m}</th>`).join("")}
                                ${modeNames.map(m => `<th style="padding: 7px;text-align: center; border:1px solid #24326a; writing-mode:vertical-rl; transform: rotate(180deg); white-space:nowrap;">${m}</th>`).join("")}
                                ${modeNames.map(m => `<th style="padding: 7px;text-align: center; border:1px solid #24326a; writing-mode:vertical-rl; transform: rotate(180deg); white-space:nowrap;">${m}</th>`).join("")}
                            </tr>
                        `;

                        $("#ANNUALCARDREPORT thead").html(thead);

                        // ===================================
                        // BODY BUILD
                        // ===================================
                        let tbody = "";
                        let grandTotalFull = 0;
                        let grandTotalObtained = 0;

                        subjects.forEach(sub => {

                            let halfTotal = 0;
                            let annualTotal = 0;
                            let finalTotal = 0;

                            let row = `
                                <tr style="height: 2.5rem; font-size: 0.9rem;">
                                    <td style="text-align:left; border:1px solid #ccc;">
                                        <span style="
                                            margin-left:10px;
                                            font-size:15px;
                                            font-weight:500;
                                            font-family:'Georgia', serif;
                                            color:${sub.is_optional ? "#d7a900" : sub.is_not_countable ? "red" : "black"};
                                        ">
                                            <input type="hidden" name="subjects_id[]" value="${sub.id}">
                                            ${sub.name}${sub.is_optional ? " (Optional)" : sub.is_not_countable ? " (Not Countable)" : ""}
                                        </span>
                                    </td>

                                    <td style="text-align:center; border:1px solid #ccc;">${fmt(sub.full_marks)}</td>
                            `;

                            // ---------------------------
                            // 1️⃣ Half Actual
                            // ---------------------------
                            modeNames.forEach(mode => {
                                const o = sub.modes[mode] || {};
                                const v = Number(o.half_actual ?? 0);
                                halfTotal += v;
                                row += `<td style="text-align:center; border:1px solid #ccc;">${fmt(v)}</td>`;
                            });
                            row += `<td style="text-align:center; font-weight:bold; border:1px solid #ccc;">${fmt(halfTotal)}</td>`;

                            // ---------------------------
                            // 2️⃣ Annual Actual
                            // ---------------------------
                            modeNames.forEach(mode => {
                                const o = sub.modes[mode] || {};
                                const v = Number(o.annual_actual ?? 0);
                                annualTotal += v;
                                row += `<td style="text-align:center; border:1px solid #ccc;">${fmt(v)}</td>`;
                            });
                            row += `<td style="text-align:center; font-weight:bold; border:1px solid #ccc;">${fmt(annualTotal)}</td>`;

                            // ---------------------------
                            // 3️⃣ Half %
                            // ---------------------------
                            modeNames.forEach(mode => {
                                const o = sub.modes[mode] || {};
                                const v = Number(o["40% of Half Yearly Exam"] ?? 0);
                                row += `<td style="text-align:center; border:1px solid #ccc;">${fmt(v)}</td>`;
                            });

                            // ---------------------------
                            // 4️⃣ Annual %
                            // ---------------------------
                            modeNames.forEach(mode => {
                                const o = sub.modes[mode] || {};
                                const v = Number(o["60% of Annual Exam"] ?? 0);
                                row += `<td style="text-align:center; border:1px solid #ccc;">${fmt(v)}</td>`;
                            });

                            // ---------------------------
                            // 5️⃣ Final (Per Mode)
                            // ---------------------------
                            modeNames.forEach(mode => {
                                const o = sub.modes[mode] || {};
                                const v = Number(o["Total mode_names Marks"] ?? 0);
                                finalTotal += v;
                                row += `<td style="text-align:center; font-weight:bold; border:1px solid #ccc;">${fmt(v)}</td>`;
                            });

                            const gpDisplay =
                                typeof sub.gp === "number" ? fmt(sub.gp) : sub.gp;

                            // ---------------------------
                            // Close row
                            // ---------------------------
                            row += `
                                <td style="text-align:center; font-weight:bold; border:1px solid #ccc;">${fmt(finalTotal)}</td>
                                <td style="text-align:center; border:1px solid #ccc;">${sub.letter_grade}</td>
                                <td style="text-align:center; border:1px solid #ccc;">${gpDisplay}</td>
                            </tr>
                            `;

                            tbody += row;

                            grandTotalFull += sub.full_marks;
                            grandTotalObtained += finalTotal;
                        });

                        // ===================================
                        // TOTAL ROW
                        // ===================================
                        tbody += `
                            <tr style="font-weight:bold; height: 2.5rem; font-size: 0.95rem;">
                                <td style="text-align:right; border:1px solid #ccc;">Total Marks:</td>
                                <td style="text-align:center; border:1px solid #ccc;">${fmt(grandTotalFull)}</td>
                                <td colspan="${modeNames.length + 1 + modeNames.length + 1 + (modeNames.length * 3)}" style="border:1px solid #ccc;"></td>
                                <td style="text-align:center; border:1px solid #ccc;">${fmt(grandTotalObtained)}</td>
                                <td style="border:1px solid #ccc;"></td>
                                <td style="border:1px solid #ccc;"></td>
                            </tr>
                        `;

                        $("#ANNUALCARDREPORT tbody").html(tbody);

                        // ===================================
                        // FORM FIELDS
                        // ===================================
                        $("#id_total_obtained_marks").val(
                            fmt(response.total_obtained_marks ?? 0)
                        );

                        $("#id_is_average_gpa").val(
                            typeof response.average_gpa === "number"
                                ? fmt(response.average_gpa)
                                : response.average_gpa
                        );

                        $("#id_average_letter_grade").val(response.average_letter_grade);
                        $("#id_result_status").val(response.result_status);
                        $("#id_is_remarks").val(response.remarks_status);
                    },

                    error: function () {
                        toastr.error("Error loading results.");
                    }
                });
            }
        });



@csrf_exempt
@login_required()
def annualResultsCardReportsManagerAPI(request):
    if request.method != 'POST':
        return HttpResponse("Invalid request")

    import json
    from django.template.loader import render_to_string
    from django.db.models import Case, When, Value, IntegerField
    from django.db.models.functions import Cast

    print_blocks = request.POST.get("print_blocks")

    try:
        blocks = json.loads(print_blocks)
    except:
        return HttpResponse("Invalid JSON")

    rendered_pages = []

    for block in blocks:

        org_id      = block.get("org_id")
        branch_id   = block.get("branch_id")
        class_id    = block.get("class_id")
        shift_id    = block.get("shift_id")
        groups_id   = block.get("groups_id")
        is_year     = block.get("is_year")
        is_version  = block.get("is_version")
        merit_id    = block.get("merit_id")
        reg_ids     = block.get("reg_ids", [])
        section_ids = block.get("section_ids", [])

        # version detect
        is_english = True if is_version == "english" else False
        is_bangla  = True if is_version == "bangla" else False
        
        final_response = {}

        # ================================
        # Fetch all merit positions for given merit_id at once
        # ================================
        merit_qs = in_merit_position_approvaldtls.objects.filter(
            merit_id=merit_id,
            reg_id__in=reg_ids
        ).values("reg_id", "merit_position")

        merit_dict = {item["reg_id"]: item["merit_position"] or 0 for item in merit_qs}

        # Sort reg_ids by merit_position ascending
        reg_ids_sorted = sorted(
            reg_ids, key=lambda rid: merit_dict.get(rid, float('inf'))
        )

        for reg_id in reg_ids_sorted:

            merit_position = merit_dict.get(reg_id, 0)

            # ================================
            # FILTER RESULT CARD ENTRY
            # ================================
            card_entry = in_results_card_entry.objects.filter(
                reg_id=reg_id,
                org_id=org_id,
                branch_id=branch_id,
                class_id=class_id,
                shift_id=shift_id,
                groups_id=groups_id,
                is_annual=True,
            ).first()

            if not card_entry:
                continue  # skip if no card

            registration = card_entry.reg_id

            # =================================
            # Collect Grade Maps (একবারই লোড)
            # =================================
            fifty_grades = in_letter_gradeFiftyMap.objects.filter(is_active=True, org_id=org_id, class_id=class_id)
            hundred_grades = in_letter_gradeHundredMap.objects.filter(is_active=True, org_id=org_id, class_id=class_id)

            if is_english:
                fifty_grades = fifty_grades.filter(is_english=True)
                hundred_grades = hundred_grades.filter(is_english=True)
            if is_bangla:
                fifty_grades = fifty_grades.filter(is_bangla=True)
                hundred_grades = hundred_grades.filter(is_bangla=True)

            # ===============================
            # Table Data Prepare (grading scale table)
            # ===============================
            table_data = []
            all_grade_ids = set(
                list(fifty_grades.values_list("grade_id", flat=True)) + 
                list(hundred_grades.values_list("grade_id", flat=True))
            )
            grades = in_letter_grade_mode.objects.filter(grade_id__in=all_grade_ids).order_by("grade_id")

            for grade in grades:
                fifty_map = fifty_grades.filter(grade_id=grade).first()
                hundred_map = hundred_grades.filter(grade_id=grade).first()
                table_data.append({
                    "grade_name": grade.is_grade_name or "",
                    "fifty_interval": f"{fifty_map.from_marks}-{fifty_map.to_marks}" if fifty_map else "",
                    "hundred_interval": f"{hundred_map.from_marks}-{hundred_map.to_marks}" if hundred_map else "",
                    "grade_point": fifty_map.grade_point if fifty_map else (hundred_map.grade_point if hundred_map else "")
                })

            # -------------------------
            # Subjects ordering
            # -------------------------
            base_filter = {
                "class_id": registration.class_id,
                "groups_id": registration.groups_id,
                "org_id": registration.org_id,
                "is_active": True
            }
            if is_english:
                base_filter["is_english"] = True
            if is_bangla:
                base_filter["is_bangla"] = True
            
            subjects_qs = (
                in_subjects.objects
                .filter(**base_filter)
                .annotate(
                    is_numeric=Case(
                        When(subjects_no__regex=r'^\d+$', then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField(),
                    ),
                    subjects_as_int=Case(
                        When(subjects_no__regex=r'^\d+$', then=Cast('subjects_no', IntegerField())),
                        default=Value(999999999),
                        output_field=IntegerField(),
                    )
                )
                .order_by('-is_numeric', 'subjects_as_int', 'subjects_no')
            )
            
            subjects_list = []
            for s in subjects_qs:
                subjects_list.append({
                    "id": s.subjects_id,
                    "name": s.subjects_name,
                    "full_marks": s.is_marks,
                    "pass_marks": s.is_pass_marks or 0,
                    "is_applicable_pass_marks": s.is_applicable_pass_marks,
                    "is_optional": s.is_optional and s.subjects_id == registration.is_optional_sub_id,
                    "is_not_countable": s.is_not_countable,
                    "letter_grade": "",
                    "gp": "-"
                })
            
            # -------------------------
            # load percentage policy
            # -------------------------
            policy = annual_exam_percentance_policy.objects.filter(
                org_id_id=org_id,
                class_id_id=class_id
            ).first()
            half_percent = int(policy.half_yearly_per) if policy and policy.half_yearly_per else 0
            annual_percent = int(policy.annual_per) if policy and policy.annual_per else 0
            
            # -------------------------
            # load half and annual result rows
            # -------------------------
            half_qs = in_result_finalizationdtls.objects.filter(
                org_id_id=org_id,
                branch_id_id=branch_id,
                reg_id_id=reg_id,
                class_id_id=class_id,
                shifts_id_id=shift_id,
                groups_id_id=groups_id,
                finalize_year=is_year,
                is_half_yearly=True,
                is_approved=True
            ).select_related("subject_id", "def_mode_id")
            
            annual_qs = in_result_finalizationdtls.objects.filter(
                org_id_id=org_id,
                branch_id_id=branch_id,
                reg_id_id=reg_id,
                class_id_id=class_id,
                shifts_id_id=shift_id,
                groups_id_id=groups_id,
                finalize_year=is_year,
                is_yearly=True,
                is_approved=True
            ).select_related("subject_id", "def_mode_id")
            
            # -------------------------
            # build mode maps
            # -------------------------
            half_map = {}
            annual_map = {}
            mode_names_set = set()
            exam_type_name = annual_qs.first().exam_type_id.exam_type_name if annual_qs.exists() else ""  # Corrected: use empty string instead of None to avoid null
            
            for r in half_qs:
                sid = r.subject_id.subjects_id
                mode = r.is_mode_name or ""
                mode_names_set.add(mode)
                half_map.setdefault(sid, {})
                half_map[sid].setdefault(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
                half_map[sid][mode]["actual"] += float(r.is_actual_marks or 0.0)
                half_map[sid][mode]["pass"] = float(r.is_pass_marks or 0.0)
                half_map[sid][mode]["default"] = float(r.is_default_marks or 0.0)
                half_map[sid][mode]["def_mode_id"] = getattr(r.def_mode_id, "def_mode_id", None)
            
            for r in annual_qs:
                sid = r.subject_id.subjects_id
                mode = r.is_mode_name or ""
                mode_names_set.add(mode)
                annual_map.setdefault(sid, {})
                annual_map[sid].setdefault(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
                annual_map[sid][mode]["actual"] += float(r.is_actual_marks or 0.0)
                annual_map[sid][mode]["pass"] = float(r.is_pass_marks or 0.0)
                annual_map[sid][mode]["default"] = float(r.is_default_marks or 0.0)
                annual_map[sid][mode]["def_mode_id"] = getattr(r.def_mode_id, "def_mode_id", None)
            
            ordered_modes_qs = defaults_exam_modes.objects.filter(is_active=True, is_mode_name__in=list(mode_names_set)).order_by("order_by")
            mode_names_ordered = [m.is_mode_name for m in ordered_modes_qs] if ordered_modes_qs.exists() else sorted(list(mode_names_set))
            
            # -------------------------
            # Calculate per-subject totals
            # -------------------------
            final_subjects = []
            total_obtained_all_subjects = 0.0
            for sub in subjects_list:
                sid = sub["id"]
                full_marks = float(sub["full_marks"] or 0)
                pass_marks = float(sub["pass_marks"] or 0)
                is_optional = sub["is_optional"]
                is_not_countable = sub["is_not_countable"]
                is_applicable_pass_marks = sub["is_applicable_pass_marks"]
                per_mode_entries = {}
                subject_half_total = 0.0
                subject_annual_total = 0.0
                subject_modes = set()
                subject_modes.update(half_map.get(sid, {}).keys())
                subject_modes.update(annual_map.get(sid, {}).keys())
                subject_modes_ordered = [m for m in mode_names_ordered if m in subject_modes] + [m for m in subject_modes if m not in mode_names_ordered]
                total_subject_weighted = Decimal('0.00')
                failed_flag_for_subject = False
                
                for mode in subject_modes_ordered:
                    half_mode = half_map.get(sid, {}).get(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
                    annual_mode = annual_map.get(sid, {}).get(mode, {"actual": 0.0, "pass": 0.0, "default": 0.0, "def_mode_id": None})
                    half_actual = float(half_mode["actual"] or 0.0)
                    annual_actual = float(annual_mode["actual"] or 0.0)
                    subject_half_total += half_actual
                    subject_annual_total += annual_actual
                    weighted_half = (Decimal(str(half_actual)) * Decimal(str(half_percent))) / Decimal(100) if half_percent else Decimal('0.00')
                    weighted_annual = (Decimal(str(annual_actual)) * Decimal(str(annual_percent))) / Decimal(100) if annual_percent else Decimal('0.00')
                    mode_total_weighted = (weighted_half + weighted_annual).quantize(Decimal('0.01'))
                    
                    per_mode_entries[mode] = {
                        "def_mode_id": half_mode.get("def_mode_id") or annual_mode.get("def_mode_id"),
                        "half_actual": round(half_actual, 2),
                        "annual_actual": round(annual_actual, 2),
                        f"{half_percent}% of Half Yearly Exam": float(weighted_half),
                        f"{annual_percent}% of Annual Exam": float(weighted_annual),
                        "Total mode_names Marks": float(mode_total_weighted)
                    }
                    total_subject_weighted += mode_total_weighted
                    # FAIL LOGIC
                    half_pass_val = float(half_mode.get("pass") or 0.0)
                    annual_pass_val = float(annual_mode.get("pass") or 0.0)
                    if half_actual and half_pass_val and (half_actual < half_pass_val):
                        failed_flag_for_subject = True
                    if annual_actual and annual_pass_val and (annual_actual < annual_pass_val):
                        failed_flag_for_subject = True
                
                if is_applicable_pass_marks:
                    if subject_half_total and (subject_half_total < pass_marks):
                        failed_flag_for_subject = True
                    if subject_annual_total and (subject_annual_total < pass_marks):
                        failed_flag_for_subject = True
                
                total_subject_marks = float(total_subject_weighted.quantize(Decimal('0.01')))
                
                # letter & GP
                if is_not_countable:
                    letter_grade = "-"
                    gp_display = 0.0
                else:
                    filter_kwargs = {
                        "org_id_id": org_id,
                        "class_id_id": registration.class_id,
                        "from_marks__lte": total_subject_marks,
                        "to_marks__gte": total_subject_marks,
                        "is_active": True
                    }
                    if is_english:
                        filter_kwargs["is_english"] = True
                    if is_bangla:
                        filter_kwargs["is_bangla"] = True
                    
                    grade_obj = None
                    if full_marks == 100:
                        grade_obj = in_letter_gradeHundredMap.objects.filter(**filter_kwargs).first()
                    elif full_marks == 50:
                        grade_obj = in_letter_gradeFiftyMap.objects.filter(**filter_kwargs).first()
                    else:
                        grade_obj = in_letter_gradeHundredMap.objects.filter(**filter_kwargs).first() or in_letter_gradeFiftyMap.objects.filter(**filter_kwargs).first()
                    
                    if grade_obj:
                        try:
                            letter_grade = grade_obj.grade_id.is_grade_name
                        except Exception:
                            letter_grade = getattr(grade_obj, "letter_grade", "F")
                        gp_display = float(getattr(grade_obj, "grade_point", getattr(grade_obj, "gp", 0.0) or 0.0))
                    else:
                        letter_grade = "F" if failed_flag_for_subject else "F"  # Note: this seems like a potential bug in original; always "F" if no grade_obj
                    
                if failed_flag_for_subject:
                    letter_grade = "F"
                    gp_display = 0.0
                
                subject_entry = {
                    "id": sid,
                    "name": sub["name"],
                    "full_marks": full_marks,
                    "pass_marks": pass_marks,
                    "is_optional": is_optional,
                    "is_not_countable": is_not_countable,
                    "modes_ordered": subject_modes_ordered,
                    "modes": per_mode_entries,
                    "Total mode_names Marks": total_subject_marks,
                    "letter_grade": letter_grade,
                    "gp": float(gp_display)
                }
                final_subjects.append(subject_entry)
                total_obtained_all_subjects += total_subject_marks
                # TOTAL FULL MARKS (Correct)
                total_full_marks = sum(s["full_marks"] for s in final_subjects)
            
            # GPA and remarks
            total_marks = total_obtained_all_subjects
            count_subjects = 0
            total_gp = 0.0
            overall_fail_flag = False
            optional_bonus = 0.0
            for s in final_subjects:
                if s["is_not_countable"]:
                    continue
                if not s["is_optional"]:
                    count_subjects += 1
                    if isinstance(s["gp"], (int, float)):
                        total_gp += s["gp"]
                    if s["gp"] == 0.00:
                        overall_fail_flag = True
                else:
                    if isinstance(s["gp"], (int, float)):
                        bonus = s["gp"] - 2.00
                        if bonus > 0:
                            optional_bonus += bonus
                    subj_obj = next((x for x in subjects_qs if x.subjects_id == s["id"]), None)
                    if subj_obj and not subj_obj.is_optional_wise_grade_cal and s["letter_grade"] == "F":
                        overall_fail_flag = True
            
            average_gpa = (total_gp + optional_bonus) / count_subjects if count_subjects > 0 else 0.0
            if overall_fail_flag:
                average_gpa = 0.0
            if average_gpa > 5.0:
                average_gpa = 5.0
            
            # Average letter grade
            if average_gpa == 0.0:
                average_letter_grade = "F"
            elif average_gpa >= 5.0:
                average_letter_grade = "A+"
            elif average_gpa >= 4.0:
                average_letter_grade = "A"
            elif average_gpa >= 3.50:
                average_letter_grade = "A-"
            elif average_gpa >= 3.0:
                average_letter_grade = "B"
            elif average_gpa >= 2.0:
                average_letter_grade = "C"
            elif average_gpa >= 1.0:
                average_letter_grade = "D"
            else:
                average_letter_grade = "F"
            
            remarks_map = {
                "A+": "Outstanding Achievement!",
                "A": "Impressive Performance!",
                "A-": "Commendable Performance!",
                "B": "Encouraging Performance!",
                "C": "An Average Performance!",
                "D": "Needs Significant Improvement!",
                "F": "Unsatisfactory Performance!"
            }
            remarks_status = remarks_map.get(average_letter_grade, "")
            
            result_status = "Failed" if average_gpa == 0.0 and average_letter_grade == "F" else "Passed"
            
            # ===============================
            # Transaction Data
            # ===============================
            def title_case(value):
                return ' '.join(word.capitalize() for word in str(value or "").split()) if value else ''

            transaction = {
                'create_date': card_entry.create_date or '',
                'reg_id': registration.reg_id if registration else '',
                'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
                'full_name': title_case(registration.full_name),
                'roll_no': registration.roll_no or '',
                'father_name': title_case(registration.father_name),
                'mother_name': title_case(registration.mother_name),
                'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
                'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
                'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
                'total_working_days': card_entry.total_working_days or '',
                'total_present_days': card_entry.total_present_days or '',
                'is_remarks': card_entry.is_remarks or '',
                'date_of_publication': card_entry.date_of_publication or '',
                'is_average_gpa': card_entry.is_average_gpa or '',
                'average_letter_grade': card_entry.average_letter_grade or '',
                'total_obtained_marks': card_entry.total_obtained_marks or '',
                'result_status': card_entry.result_status or '',
                'merit_position': merit_position,
                'is_year': is_year,
                'merit_id': merit_id,
                "exam_type_name": exam_type_name,
            }
            
            # -------------------------
            # Response for this reg_id
            # -------------------------
            final_response[reg_id] = {
                "success": True,
                "half_percent": half_percent,
                "annual_percent": annual_percent,
                "mode_names": mode_names_ordered,
                "half_yearly_exam": [
                    {
                        "subject_id": sid,
                        "modes": half_map.get(sid, {}),
                        "subject_total_half": sum([v["actual"] for v in half_map.get(sid, {}).values()]) if half_map.get(sid) else 0.0
                    } for sid in sorted(list(half_map.keys()))
                ],
                "annual_exam": [
                    {
                        "subject_id": sid,
                        "modes": annual_map.get(sid, {}),
                        "subject_total_annual": sum([v["actual"] for v in annual_map.get(sid, {}).values()]) if annual_map.get(sid) else 0.0
                    } for sid in sorted(list(annual_map.keys()))
                ],
                "final_subjects": final_subjects,
                "total_full_marks": round(total_full_marks, 2),
                "total_obtained_marks": round(total_marks, 2),
                "average_gpa": round(average_gpa, 2),
                "average_letter_grade": average_letter_grade,
                "remarks_status": remarks_status,
                "result_status": result_status,
            }
            
            # print("final_response:", final_response[reg_id])
            

            html = render_to_string(
                'result_card_entry/annual_result_card/annual_card_report/annual_report_card_report.html',
                {
                    "transaction": transaction,
                    "registration": registration,
                    "table_data": table_data,
                    "final_response": final_response[reg_id],
                }
            )

            rendered_pages.append(html)
            
    return HttpResponse("".join(rendered_pages))


