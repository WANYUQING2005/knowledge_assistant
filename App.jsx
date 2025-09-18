/* eslint-disable no-unused-vars */
import { useState } from "react";
import { BrowserRouter } from "react-router-dom";
import HomePage from "./HomePage";
import BaseLibrary from "./BaseLibrary";
import SelectedLibrary from "./SelectedLibrary";
import { Route, Routes } from "react-router-dom";
import Login from "./Login";
import TransformImages from "./TransformImages";
import Signup from "./Signup";
import DetailLibrary from "./DetailLibrary";
import NewKnowledge from "./NewKnowledge";
import Chat from './Chat'
function App() {
  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />}>
            <Route index element={<Login />} />
            <Route path="signup" element={<Signup />} />
          </Route>
          <Route path="/baselibrary" element={<BaseLibrary />} />
          <Route path="/baselibrary/:id" element={<DetailLibrary/>}/>
          <Route path="/baselibrary/:id/upload" element={<NewKnowledge/>}/>
          <Route path='/chat' element={<Chat/>}/>
          <Route path="/selectedlibrary" element={<SelectedLibrary />} />
        </Routes>
      </BrowserRouter>
    </>
  );
}

export default App;
