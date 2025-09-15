class NursingHeader extends HTMLElement {
  constructor() {
    super();

    const shadow = this.attachShadow({ mode: 'open' });

    const indexUrl = this.getAttribute('data-index-url') || '#';
    const recordUrl = this.getAttribute('data-record-url') || '#';
    const physicianUrl = this.getAttribute('data-physician-url') || '#';
    const handoverUrl = this.getAttribute('data-handover-url') || '#';

    const style = `
      :host {
          display: block;
          width: 100%;
      }

      .topnav,
      .myTopnav,
      .imgNav {
        padding: 0 !important;
        margin: 0 !important;
      }

      #main {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 10px;
      }

      .topnav {
        background: linear-gradient(to right, #76a7c5, #5b93b3); 
        width: 100%;
        display: flex;
        justify-content: center;
        padding: 0;
        margin: 0;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); 
        height: 60px;
      }

      .myTopnav {
        display: flex;
        width: 100%;
        justify-content: space-between;
        align-items: center;
        padding: 0 20px; 
      }

      .imgNav {
        display: flex;
        width: 100%;
        height: 60px !important;
        justify-content: flex-start;
        align-items: center;
      }

      .topnav a  {
        color: white;
        text-align: center;
        padding: 18px 30px; 
        text-decoration: none;
        font-size: 18px;
        font-weight: bold;
        display: block;
        transition: transform 0.2s ease; 
        height: 60px !important;
        line-height: 1.2;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: pre-line;
      }

      .tt {
        background-color: rgba(255, 255, 255, 0.2); 
        color: white;
        text-align: center;
        padding: 18px 30px; 
        text-decoration: none;
        font-size: 18px;
        font-weight: bold;
        display: block;
        transition: transform 0.2s ease; 
        height: 60px !important;
        line-height: 1.2;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: pre-line;
      }

      .tt1 {
        background-color: transparent;
      }

      .topnav a:hover {
        transform: translateY(-2px);
      }

      @media screen and (max-width: 1200px) {
        .myTopnav {
          width: 100%;
          max-width: unset;
          padding: 0 10px;
        }

        .topnav a {
          font-size: 16px;
          padding: 15px 20px;
        }

        .tt1 {
          margin-left: 5px;
        }
      }
    `;

    const html = `
      <div id="main">
        <div class="topnav">
          <div class="myTopnav">
            <div class="imgNav">
              <p class="tt">Nursing Record Query System</p>
              <a href="${indexUrl}" class="tt1">Enter\nData</a>
              <a href="${recordUrl}" class="tt1">Nursing\nRecord</a>
              <a href="${physicianUrl}" class="tt1">Physician\nNotes</a>
              <a href="${handoverUrl}" class="tt1">Shift\nHandover</a>
            </div>
          </div>
        </div>
      </div> 
    `;

    shadow.innerHTML = `<style>${style}</style>${html}`;
  }
}

customElements.define('n-header', NursingHeader);
