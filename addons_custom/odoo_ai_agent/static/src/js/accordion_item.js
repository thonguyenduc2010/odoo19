/** @odoo-module **/

import { Component, useState,useEffect,useRef,onPatched,onWillRender } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ViewButton } from '@web/views/view_button/view_button';
import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { usePopover } from "@web/core/popover/popover_hook";
import { session } from "@web/session";

export class AccordionItem extends Component {
  setup() {
    // this.state = useState();
    this.orm = useService('orm')
    this.action = useService('action')
    this.PlanAccordionItemWraper = useRef("plan_according_item_wrapper")
    this.text_delay = 1;
    this.planItemContent = useRef("plan_item_content")
    this.feedbackEl = useRef("feedbackEl");
    // this.bistaLoader = useRef("bistaLoader");
    // this.owlCarouselCount = 0;
    onWillRender(() => {
      var outputResponse = this.props.data.output_response;
      var templateId = this.props.data.template_id;
      if (templateId && typeof outputResponse === 'string') {
        outputResponse = outputResponse
    .replace(/\\/g, '\\\\') // escape backslashes first
    .replace(/["']/g, match => match === '"' ? '\\""' : '"');
        // outputResponse = outputResponse.replace(/'/g, '"')
        outputResponse = outputResponse.replace(/^"(.*)"$/, "'$1'");
        this.props.data.output_response = JSON.parse(outputResponse);
      }
    });
    useEffect(
      () => {
        var self = this;
        var isTable = false;
        var body = this.PlanAccordionItemWraper.el.querySelector(".accordion-body")
        body.querySelectorAll("table").forEach((table) => {
          let rows = table.querySelectorAll("table tr");
          var initial_rows = 10; // Number of rows to show initially
          if (rows.length > initial_rows) {
              rows.forEach((row, index) => {
                  if (index == initial_rows) row.style.opacity = "50%";
                  if (index > initial_rows) row.style.display = "none";
              });
  
              let buttonContainer = document.createElement("div");
              buttonContainer.classList.add("view-more-container");

              let button = document.createElement("button");
              button.textContent = "Click more to view";
              button.classList.add("view-more-btn");

              buttonContainer.appendChild(button);
  
              
              table.parentNode.insertBefore(buttonContainer, table.nextSibling);
              let currentIndex = initial_rows+1;
  
              
              button.addEventListener("click", function () {
                  let rowsToShow = 10; // Number of rows to reveal per click
                  for (let i = 0; i < rowsToShow; i++) {
                      rows[currentIndex-1].style.opacity = "100%";
                      if (currentIndex < rows.length) {
                          rows[currentIndex].style.display = "table-row"; 
                          if (currentIndex != rows.length-1) {
                            rows[currentIndex].style.opacity = "50%";
                          }
                          currentIndex++;
                      }
                  }
  
                  // Remove button if all rows are visible
                  if (currentIndex >= rows.length) {
                      button.remove();
                  }
              });
          }
        });
      },
      () => [this.props.data.title]
    )
  }

  toggleReletedTable(ev){
    ev.stopPropagation();
    const tableContainer = ev.currentTarget.closest('.vendor_wrapper').querySelector('.ai-agent-response-table-container');
    if (tableContainer) {
      tableContainer.classList.toggle('d-none');
      const icon = ev.currentTarget.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-eye-slash');
        icon.classList.toggle('fa-eye');
      }
    }
  }

  evalInvisible(invisible, record) {
        return evaluateBooleanExpr(invisible, record.evalContextWithVirtualIds);
    }
  
  async onClickDownloadAgentPDF(ev){
    var self = this;
    var action = await self.orm.call("agent.response.history.step", "action_download_pdf", [self.props.record.resId])
    if (action) {
      self.action.doAction(action);
    }
  }

  async onClickDownloadAgentExcel(ev){
    var self = this;
    var action = await self.orm.call("agent.response.history.step", "action_download_excel", [self.props.record.resId])
    if (action) {
      self.action.doAction(action);
    }
  }

  static components = { ViewButton };
  static template = "accordion_item_field";
  static props = [ "accordion_id","label", "content","buttons","record", "has_user_confirmation","data" ]
}
